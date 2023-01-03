#[macro_use]
mod utils;
mod auth;

use std::sync::Arc;

use auth::Authenticated;
use axum::{
    extract::{ConnectInfo, FromRef, Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use axum_extra::extract::{
    cookie::{Cookie, Key, PrivateCookieJar},
    CookieJar,
};
use common::{
    LoginError, LoginRequest, LoginResponse, LoginSuccess, Test1, USERNAME_ID_COOKIE,
    USER_ID_COOKIE,
};
use hyper::{Body, Request};
use std::net::SocketAddr;
use tower::Service;
use tower_http::services::ServeDir;
use tracing::{error, event, info, trace, warn};
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

async fn api_test1(ConnectInfo(addr): ConnectInfo<SocketAddr>) -> impl IntoResponse {
    let time = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    info!(target: "api_test1", addr = addr.to_string(), time);
    return Json(Test1 { number: time });
}

async fn api_test2(ConnectInfo(addr): ConnectInfo<SocketAddr>) -> impl IntoResponse {
    let random = rand::random::<u64>();

    info!(target: "api_test2", addr = addr.to_string(), random);

    return Json(Test1 { number: random });
}

// TODO: de-duplicate cookie code with a new struct that contains both private and regular jars
#[axum::debug_handler]
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
                println!("your user ID cookie: {}", cookie);

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
                eprintln!("no valid user_id cookie or body?");
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
    let user = Authenticated { id: 1 };
    let login_result = LoginResponse::Success(LoginSuccess { id: user.id });
    (private_cookies, regular_cookies) = user.cookies(private_cookies, regular_cookies);

    return (
        StatusCode::OK,
        private_cookies,
        regular_cookies,
        Json(login_result),
    );
}

// TODO: use DB to check
fn get_user_from_cookie(cookie: &Cookie) -> Option<Authenticated> {
    return Some(Authenticated { id: 1 });
}

fn wipe_cookies(private: PrivateCookieJar, regular: CookieJar) -> (PrivateCookieJar, CookieJar) {
    let private = private.remove(Cookie::named(USER_ID_COOKIE));
    let regular = regular.remove(Cookie::named(USERNAME_ID_COOKIE));

    return (private, regular);
}

#[axum::debug_handler]
// TODO: access database
async fn logout(
    State(_): State<BackendState>, // for cookie jar key
    private_cookies: PrivateCookieJar,
    regular_cookies: CookieJar,
) -> impl IntoResponse {
    // for now, just tell client to wipe all cookies
    let (private_cookies, regular_cookies) = wipe_cookies(private_cookies, regular_cookies);
    return (StatusCode::OK, private_cookies, regular_cookies);
}

#[tokio::main]
async fn main() {
    setup_tracing();

    let frontend_state = Arc::new(FrontendState {
        serve_dir: tokio::sync::Mutex::new(ServeDir::new(relative_path(FRONTEND_PATH))),
    });

    let backend_state = BackendState {
        // TODO: load key from file/environmental variable
        key: Key::from(DEV_RANDOM_STR.as_bytes()),
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
        .with_state(backend_state);

    axum::Server::bind(&"0.0.0.0:8000".parse().expect("unable to bind"))
        .serve(app.into_make_service_with_connect_info::<SocketAddr>())
        .await
        .expect("unable to serve");
}

#[derive(Clone)]
struct BackendState {
    // private cookie key
    key: Key,
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
async fn frontend_handler(
    path: Option<Path<String>>, // option since we need to handle the root path
    State(frontend_state): State<Arc<FrontendState>>,
    ConnectInfo(addr): ConnectInfo<SocketAddr>,
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

    // info!(target: "frontend_handler", addr = addr.to_string(), real_path);

    // create request to pass to tower_http's ServeDir
    let req = Request::builder()
        .uri(real_path.clone())
        .body(Body::empty())
        .map_err(|e| {
            error!(target: "frontend_handler", addr = addr.to_string(), real_path, "Request::builder error: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // pass request to ServeDir service
    match frontend_state.serve_dir.lock().await.call(req).await {
        // will be a 404 if file not found
        Ok(res) => {
            // TODO: figure out dynamic level for trace!, could be done via macro
            if res.status().is_success() {
                info!(target: "frontend_handler", addr = addr.to_string(), real_path, status = res.status().as_str());
            } else {
                warn!(target: "frontend_handler", addr = addr.to_string(), real_path, status = res.status().as_str());
            };

            return Ok(res);
        }
        Err(e) => {
            error!(target: "frontend_handler", addr = addr.to_string(), real_path, "ServeDir error: {}", e);
            return Err(StatusCode::NOT_FOUND);
        }
    }
}
