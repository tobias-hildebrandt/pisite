mod cookies;
mod db;
mod endpoints;
mod utils;

use axum::{
    extract::{ConnectInfo, State},
    response::IntoResponse,
    routing::{get, post},
    Router,
};
use axum_extra::extract::cookie::{Key, PrivateCookieJar};
use common::{setup_tracing, SESSION_COOKIE};
use endpoints::{backend_state::BackendState, frontend::FrontendState};
use std::net::SocketAddr;
use std::sync::Arc;
use tower_http::services::ServeDir;
use tracing::{error, info, instrument, warn, Instrument};
use utils::{api_route, relative_path};

// TODO: set up env var or config file instead of consts
const API_PREFIX: &str = "/api/";
const FRONTEND_PATH: &str = "../web-frontend/dist/";
const DEV_RANDOM_STR: &str =
    "dN4lzNFFv9AAzK+yuIyO9al8HFIxLJcb0YD6kTeQ3I10+keQf+dvPh8ggY3/CW/ObA18Zf/kXU9c
rsyepZ66ZX/QijLclJ35l0BLO7F2KIPqek1Txiz/wpuflkz/f1b6baUOJsySqUjpoTCz2P5diEMn
uBIocI1H7Ds4ULVBJp+gXNs2630JI1bLeruhys+oS+PlIowQE7oqx83jPT/WLlb3vpX9tEz3erJb
zqfeRqM/cFbbo/1HEPDQfOPMuciItwXUyQB11/djx30SciCibwUJo2fBtrx/O2iESMxqfMbLTQel
3yeikhsB67AndYMi9s8nFbpyYkolCEIE5xsqm/vVZMd18H01Fh5nfkLpOFMYod/iWKumxDWOMe/h
auA4/WB6MyUilBH8q/LhFIw0YStTXBc/1/RJu/1tgPYK64WM5X812TXcvcaJBbATtQHGpQ+B4IEu
oqCK+Ec/XpWnObj8vA+oq56w+WfRzDnaPF09/oRxYKfB6CCYfo";
const BIND_PORT: &str = "8000";

#[derive(thiserror::Error, Debug)]
enum RunError {
    #[error("DBError {0:?}")]
    DBError(db::DBError),
    #[error("ServeError {0:?}")]
    ServeError(hyper::Error),
}

#[tokio::main]
#[instrument]
async fn main() -> Result<(), RunError> {
    setup_tracing();

    // states
    let frontend_state = Arc::new(FrontendState {
        serve_dir: tokio::sync::Mutex::new(ServeDir::new(relative_path(FRONTEND_PATH))),
    });

    let backend_state = BackendState {
        // TODO: load key from file/environmental variable
        key: Key::from(DEV_RANDOM_STR.as_bytes()),
        connection_pool: db::init_and_get_connection_pool().map_err(RunError::DBError)?,
    };

    let app = Router::new();

    // TODO: serve these via an http server
    // frontend routes
    let app = app
        .route("/", get(endpoints::frontend::frontend_handler))
        .route("/:path", get(endpoints::frontend::frontend_handler))
        .with_state(frontend_state);

    // TODO: make sure these work with a reverse proxy
    // backend routes
    let app = app
        .route(
            &api_route(API_PREFIX, "test1"),
            get(endpoints::testing::api_test1),
        )
        .route(
            &api_route(API_PREFIX, "test2"),
            get(endpoints::testing::api_test2),
        )
        .route(
            &api_route(API_PREFIX, "test3"),
            get(endpoints::testing::api_test3),
        )
        .route(
            &api_route(API_PREFIX, "login"),
            post(endpoints::auth::login),
        )
        .route(
            &api_route(API_PREFIX, "logout"),
            post(endpoints::auth::logout),
        )
        .route(
            &api_route(API_PREFIX, "whoami"),
            get(endpoints::auth::whoami),
        )
        .with_state(backend_state.clone());

    // add request tracing
    let app = app.layer(axum::middleware::from_fn_with_state(
        backend_state.clone(),
        add_trace_layer,
    ));

    info!("starting server @ http://localhost:{}", BIND_PORT);

    axum::Server::bind(
        &format!("0.0.0.0:{}", BIND_PORT)
            .parse()
            .expect("unable to bind"),
    )
    .serve(app.into_make_service_with_connect_info::<SocketAddr>())
    .await
    .map_err(RunError::ServeError)?;

    Ok(())
}

async fn add_trace_layer<B>(
    State(BackendState {
        key,
        connection_pool,
    }): State<BackendState>,
    ConnectInfo(addr): ConnectInfo<SocketAddr>,

    request: hyper::Request<B>,
    next: axum::middleware::Next<B>,
) -> impl IntoResponse {
    // extract information
    let method = request.method().as_str();
    let path = request.uri().path();
    let headers = request.headers();

    // extract session cookie using state key
    let private_cookies = PrivateCookieJar::from_headers(headers, key);

    let session_id_str = private_cookies
        .get(SESSION_COOKIE)
        .map(|cookie| cookie.value().to_string());

    let session_id = session_id_str.clone().and_then(|s| s.parse::<i32>().ok());

    // TODO: get user from DB?
    let user_str: String = session_id
        .and_then(|session_id| {
            Some(
                match (|| {
                    let mut conn = connection_pool.get()?;
                    let (_session, user) = db::get_session(&mut conn, session_id)?;

                    Ok::<String, anyhow::Error>(user.username)
                })() {
                    Ok(u) => u,
                    Err(e) => format!("Error getting user: {:?}", e),
                },
            )
        })
        .unwrap_or_else(|| "no user".to_string());

    // put it in a span
    let span = tracing::span!(
        tracing::Level::INFO,
        "http",
        a = addr.to_string(),
        m = method,
        p = path,
        s = session_id_str.unwrap_or_else(|| "no session".to_string()),
        u = user_str
    );

    // run the next middleware with the span
    let after_next = next.run(request).instrument(span.clone()).await;

    // make sure we log something
    if !after_next.status().is_success() {
        let _e = span.enter();

        let status_num = after_next.status().as_u16();

        let status_str = after_next
            .status()
            .canonical_reason()
            .and_then(|c| Some(c.to_string()))
            .unwrap_or_else(|| "unknown".to_string());

        warn!(status = status_num, status_str);
    }

    return after_next;
}
