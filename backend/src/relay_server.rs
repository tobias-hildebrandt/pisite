mod auth;
mod db;
mod utils;

use std::sync::Arc;

use auth::Authenticated;
use axum::{
    extract::{ConnectInfo, FromRef, Path, State},
    http::StatusCode,
    response::{ErrorResponse, IntoResponse},
    routing::{get, post},
    Json, Router,
};
use axum_extra::extract::{
    cookie::{Cookie, Expiration, Key, PrivateCookieJar},
    CookieJar,
};
use common::{
    LoginError, LoginRequest, LoginResponse, LoginSuccess, Test1, USERNAME_ID_COOKIE,
    USER_ID_COOKIE,
};
use hyper::{Body, Method, Request};
use std::net::SocketAddr;
use time::OffsetDateTime;
use tower::Service;
use tower_http::services::ServeDir;
use tracing::{error, info, instrument, warn, Instrument};
use utils::{api_route, relative_path, setup_tracing};

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

#[axum::debug_handler]
#[instrument]
async fn api_test1() -> impl IntoResponse {
    let time = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    info!(time);
    return Json(Test1 { number: time });
}

#[axum::debug_handler]
#[instrument]
async fn api_test2() -> impl IntoResponse {
    let random = rand::random::<u64>();

    info!(random);

    return Json(Test1 { number: random });
}

#[axum::debug_handler]
#[instrument(skip(connection_pool))]
async fn api_test3(
    State(BackendState {
        key: _,
        connection_pool,
    }): State<BackendState>,
) -> Result<impl IntoResponse, ErrorResponse> {
    let mut connection = connection_pool.get()?;

    let users = db::get_all_users(&mut connection)?;

    let all_users_string = users
        .into_iter()
        .map(|u| format!("user({}, {})", u.id, u.username))
        .fold(String::new(), |mut accum, new| {
            accum.push_str(&new);
            accum.push_str(", ");
            accum
        });

    info!("success");

    let response = (StatusCode::OK, all_users_string).into_response();
    Ok(response)
}

// TODO: de-duplicate cookie code with a new struct that contains both private and regular jars
// TODO: format and log relevant cookies
#[axum::debug_handler]
#[instrument(skip(private_cookies, regular_cookies))]
async fn login(
    State(_): State<BackendState>, // for cookie jar key
    private_cookies: PrivateCookieJar,
    regular_cookies: CookieJar,
    login_req: Option<Json<LoginRequest>>,
) -> impl IntoResponse {
    // mutable
    let (mut private_cookies, mut regular_cookies) = (private_cookies, regular_cookies);

    //no body
    if login_req.is_none() {
        match private_cookies.get(USER_ID_COOKIE) {
            Some(cookie) => {
                // you sent us a user ID cookie and no body
                let u = get_user_from_cookie(&cookie);

                match u {
                    Some(auth) => {
                        // wipe old cookie
                        (private_cookies, regular_cookies) =
                            wipe_cookies(private_cookies, regular_cookies);

                        // set your new cookies
                        (private_cookies, regular_cookies) =
                            auth.cookies(private_cookies, regular_cookies);
                    }
                    None => {
                        // your cookie is invalid
                        // wipe old cookie
                        (private_cookies, regular_cookies) =
                            wipe_cookies(private_cookies, regular_cookies);

                        warn!(e = "invalid cookie, wiping");

                        return (
                            StatusCode::FORBIDDEN,
                            private_cookies,
                            regular_cookies,
                            Json(LoginResponse::Error(LoginError::InvalidData)),
                        );
                    }
                }
            }
            None => {
                // no cookies and no body??
                warn!(e = "no valid user_id cookie or body, wiping");

                // delete any id cookie you have
                (private_cookies, regular_cookies) = wipe_cookies(private_cookies, regular_cookies);
                return (
                    StatusCode::BAD_REQUEST,
                    private_cookies,
                    regular_cookies,
                    Json(LoginResponse::Error(LoginError::InvalidData)),
                );
            }
        }
    }
    // TODO: get from DB using login_req
    let authenticated = Authenticated { id: 1 };
    let login_result = LoginResponse::Success(LoginSuccess {
        id: authenticated.id,
    });
    (private_cookies, regular_cookies) = authenticated.cookies(private_cookies, regular_cookies);

    info!(authenticated.id = authenticated.id);

    return (
        StatusCode::OK,
        private_cookies,
        regular_cookies,
        Json(login_result),
    );
}

// TODO: use DB to check
fn get_user_from_cookie(_cookie: &Cookie) -> Option<Authenticated> {
    return Some(Authenticated { id: 1 });
}

fn wipe_cookies(private: PrivateCookieJar, regular: CookieJar) -> (PrivateCookieJar, CookieJar) {
    // remove old cookies
    let private = private.remove(Cookie::named(USER_ID_COOKIE));
    let regular = regular.remove(Cookie::named(USERNAME_ID_COOKIE));

    // add regular blank cookies that have already expired
    let mut user_id = Cookie::new(USER_ID_COOKIE, "");
    user_id.set_expires(Expiration::from(OffsetDateTime::UNIX_EPOCH));

    let mut username = Cookie::new(USERNAME_ID_COOKIE, "");
    username.set_expires(Expiration::from(OffsetDateTime::UNIX_EPOCH));

    let regular = regular.add(user_id);
    let regular = regular.add(username);

    return (private, regular);
}

// TODO: access database
// TODO: format and log relevant cookies
#[axum::debug_handler]
#[instrument(skip(private_cookies, regular_cookies))]
async fn logout(
    State(_): State<BackendState>, // for cookie jar key
    private_cookies: PrivateCookieJar,
    regular_cookies: CookieJar,
) -> impl IntoResponse {
    match private_cookies.get(USER_ID_COOKIE) {
        Some(c) => match get_user_from_cookie(&c) {
            Some(user) => {
                info!(user.id = user.id);
            }
            None => {
                warn!(e = "had invalid id cookie");
            }
        },
        None => {
            warn!(e = "had no private user id cookie");
        }
    }

    // for now, just tell client to wipe all cookies
    let (private_cookies, regular_cookies) = wipe_cookies(private_cookies, regular_cookies);
    return (StatusCode::OK, private_cookies, regular_cookies);
}

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
        .route("/", get(frontend_handler))
        .route("/:path", get(frontend_handler))
        .with_state(frontend_state);

    // backend routes
    let app = app
        .route(&api_route(API_PREFIX, "test1"), get(api_test1))
        .route(&api_route(API_PREFIX, "test2"), get(api_test2))
        .route(&api_route(API_PREFIX, "login"), post(login))
        .route(&api_route(API_PREFIX, "logout"), post(logout))
        .route(&api_route(API_PREFIX, "test3"), get(api_test3))
        .with_state(backend_state);

    // add request tracing
    let app = app.layer(axum::middleware::from_fn(add_trace_layer));

    axum::Server::bind(&"0.0.0.0:8000".parse().expect("unable to bind"))
        .serve(app.into_make_service_with_connect_info::<SocketAddr>())
        .await
        .map_err(RunError::ServeError)?;

    Ok(())
}

async fn add_trace_layer<B>(
    ConnectInfo(addr): ConnectInfo<SocketAddr>,
    request: hyper::Request<B>,
    next: axum::middleware::Next<B>,
) -> impl IntoResponse {
    // extract information
    let method = request.method().as_str();
    let path = request.uri().path();
    let headers = request.headers();
    let user_id = headers
        .get(USER_ID_COOKIE)
        .map(|h| h.to_str().unwrap_or("non-ascii"))
        .unwrap_or("none");

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

#[derive(Clone)]
struct BackendState {
    // private cookie key
    key: Key,
    // arc mutex for the database connection
    // (sqlite does not support multiple writers)
    connection_pool: db::ConnPool,
}

// so our signed cookie jar can get the key from the backend state
impl FromRef<BackendState> for Key {
    fn from_ref(state: &BackendState) -> Self {
        state.key.clone()
    }
}

struct FrontendState {
    serve_dir: tokio::sync::Mutex<ServeDir>,
}

// TODO: improve performance by allowing simulatenous reads
// TODO: sanitize input to avoid ../ or similar
// maybe switch to oneshot or cache files at launch?
#[instrument(skip_all)]
async fn frontend_handler(
    path: Option<Path<String>>, // option since we need to handle the root path
    State(frontend_state): State<Arc<FrontendState>>,
) -> impl IntoResponse {
    // handle serving from /
    let real_path = match path {
        Some(Path(path)) => {
            if path.eq("") || path.eq("/") {
                "/index.html".to_string()
            } else {
                format!("/{}", path)
            }
        }
        None => "/index.html".to_string(),
    };

    // create request to pass to tower_http's ServeDir
    let req = Request::builder()
        .uri(real_path)
        .body(Body::empty())
        .map_err(|e| {
            error!("Request::builder error: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // pass request to ServeDir service
    match frontend_state.serve_dir.lock().await.call(req).await {
        // will be a 404 if file not found
        Ok(res) => {
            // TODO: figure out dynamic level for trace!, could be done via macro
            if res.status().is_success() {
                info!(status = res.status().as_str());
            } else {
                warn!(status = res.status().as_str());
            };

            return Ok(res);
        }
        Err(e) => {
            error!("ServeDir error: {}", e);
            return Err(StatusCode::NOT_FOUND);
        }
    }
}
