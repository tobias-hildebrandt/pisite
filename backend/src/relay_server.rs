mod cookies;
mod db;
mod endpoints;
mod utils;
mod crypt;

use axum::{
    extract::{ConnectInfo, State},
    response::IntoResponse,
    routing::{get, post},
    Router,
};
use axum_extra::extract::cookie::{Key, PrivateCookieJar};
use common::USER_ID_COOKIE;
use endpoints::{backend_state::BackendState, frontend::FrontendState};
use std::net::SocketAddr;
use std::sync::Arc;
use tower_http::services::ServeDir;
use tracing::{error, instrument, warn, Instrument};
use utils::{api_route, relative_path, setup_tracing};

// TODO: set up env var or config file instead of consts
const API_PREFIX: &str = "/api/";
const FRONTEND_PATH: &str = "../frontend/dist/";
const DEV_RANDOM_STR: &str =
    "dN4lzNFFv9AAzK+yuIyO9al8HFIxLJcb0YD6kTeQ3I10+keQf+dvPh8ggY3/CW/ObA18Zf/kXU9c
rsyepZ66ZX/QijLclJ35l0BLO7F2KIPqek1Txiz/wpuflkz/f1b6baUOJsySqUjpoTCz2P5diEMn
uBIocI1H7Ds4ULVBJp+gXNs2630JI1bLeruhys+oS+PlIowQE7oqx83jPT/WLlb3vpX9tEz3erJb
zqfeRqM/cFbbo/1HEPDQfOPMuciItwXUyQB11/djx30SciCibwUJo2fBtrx/O2iESMxqfMbLTQel
3yeikhsB67AndYMi9s8nFbpyYkolCEIE5xsqm/vVZMd18H01Fh5nfkLpOFMYod/iWKumxDWOMe/h
auA4/WB6MyUilBH8q/LhFIw0YStTXBc/1/RJu/1tgPYK64WM5X812TXcvcaJBbATtQHGpQ+B4IEu
oqCK+Ec/XpWnObj8vA+oq56w+WfRzDnaPF09/oRxYKfB6CCYfo";

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

    // frontend routes
    let app = app
        .route("/", get(endpoints::frontend::frontend_handler))
        .route("/:path", get(endpoints::frontend::frontend_handler))
        .with_state(frontend_state);

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

    axum::Server::bind(&"0.0.0.0:8000".parse().expect("unable to bind"))
        .serve(app.into_make_service_with_connect_info::<SocketAddr>())
        .await
        .map_err(RunError::ServeError)?;

    Ok(())
}

async fn add_trace_layer<B>(
    State(BackendState {
        key,
        connection_pool: _connection_pool,
    }): State<BackendState>,
    ConnectInfo(addr): ConnectInfo<SocketAddr>,

    request: hyper::Request<B>,
    next: axum::middleware::Next<B>,
) -> impl IntoResponse {
    // extract information
    let method = request.method().as_str();
    let path = request.uri().path();
    let headers = request.headers();

    // extract user_id cookie using state key
    let private_cookies = PrivateCookieJar::from_headers(headers, key);
    let user_id = match private_cookies.get(USER_ID_COOKIE) {
        Some(c) => c.value().to_string(),
        None => "none".to_string(),
    };

    // TODO: get user from DB?

    // put it in a span
    let span = tracing::span!(
        tracing::Level::INFO,
        "http",
        a = addr.to_string(),
        m = method,
        p = path,
        u = user_id
    );

    // run the next middleware with the span
    let after_next = next.run(request).instrument(span).await;

    return after_next;
}
