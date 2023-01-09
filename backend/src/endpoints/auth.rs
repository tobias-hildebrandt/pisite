use axum::{extract::State, response::IntoResponse, Json};
use axum_extra::extract::{CookieJar, PrivateCookieJar};
use common::{LoginRequest, LoginSuccess, USER_ID_COOKIE};
use hyper::StatusCode;
use tracing::{error, info, instrument, warn};

use crate::{cookies::get_wiped_cookie_jar, db, BackendState};

// TODO: add session tracking to DB?
#[axum::debug_handler]
#[instrument(skip_all, fields(attempted))]
pub async fn login(
    State(BackendState {
        key: _key,
        connection_pool,
    }): State<BackendState>,
    private_cookies: PrivateCookieJar,
    login_req: Json<LoginRequest>,
) -> Result<impl IntoResponse, (hyper::StatusCode, CookieJar)> {
    tracing::Span::current().record("attempted", &login_req.username);

    // closure to allow ? operator
    // TODO: convert to a try block once the feature is stabilized in rust
    let user = match (|| {
        let conn = &mut connection_pool
            .get()
            .map_err(|e| hyper::StatusCode::from(e))?;
        let user = db::attempt_login(conn, &login_req.username, &login_req.password)
            .map_err(|e| hyper::StatusCode::from(e))?;

        Ok(user)
    })() {
        Ok(u) => u,
        Err(status) => {
            return Err((status, get_wiped_cookie_jar()));
        }
    };

    // success, add real cookies
    let private_cookies = user.cookies(private_cookies);

    info!(id = user.id, username = user.username);

    return Ok((
        hyper::StatusCode::OK,
        private_cookies,
        Json(LoginSuccess {
            username: user.username,
        }),
    ));
}

// TODO: fail if not logged in?
#[axum::debug_handler]
#[instrument]
pub async fn logout() -> impl IntoResponse {
    // for now, just tell client to wipe all cookies
    let wiped = get_wiped_cookie_jar();
    info!("logged out");
    return (StatusCode::OK, wiped);
}

#[axum::debug_handler]
#[instrument(skip_all)]
pub async fn whoami(
    State(BackendState {
        key: _,
        connection_pool,
    }): State<BackendState>,
    private_cookies: PrivateCookieJar,
) -> Result<impl IntoResponse, StatusCode> {
    // check for user id cookie
    let user_id = match private_cookies.get(USER_ID_COOKIE) {
        Some(c) => c.value().to_string(),
        None => {
            warn!(e = "no id cookie");
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    // parse user id cookie
    let user_id = match user_id.parse::<i32>() {
        Ok(u) => u,
        Err(_e) => {
            warn!(e = "invalid id cookie", c = user_id);
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    // get database connection
    let mut conn = match connection_pool.get() {
        Ok(c) => c,
        Err(e) => {
            error!("{:?}", e);
            return Err(StatusCode::INTERNAL_SERVER_ERROR);
        }
    };

    // get user from DB
    let u = db::get_user_by_id(&mut conn, user_id)?;

    info!(u = u.username);

    return Ok((
        StatusCode::OK,
        Json(LoginSuccess {
            username: u.username,
        }),
    ));
}
