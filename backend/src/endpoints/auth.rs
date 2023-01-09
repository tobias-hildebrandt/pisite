use axum::{extract::State, response::IntoResponse, Json};
use axum_extra::extract::{CookieJar, PrivateCookieJar};
use common::{LoginRequest, LoginSuccess, WhoAmIResponse, USER_ID_COOKIE};
use hyper::StatusCode;
use tracing::{error, info, instrument, warn};

use crate::{cookies::wipe_cookies, db, BackendState};

// TODO: de-duplicate cookie code with a new struct that contains both private and regular jars
// TODO: format and log relevant cookies
#[axum::debug_handler]
#[instrument(skip_all, fields(attempted))]
pub async fn login(
    State(BackendState {
        key: _key,
        connection_pool,
    }): State<BackendState>,
    private_cookies: PrivateCookieJar,
    regular_cookies: CookieJar,
    login_req: Json<LoginRequest>,
) -> Result<impl IntoResponse, StatusCode> {
    tracing::Span::current().record("attempted", &login_req.username);

    // mutable
    let (mut private_cookies, mut regular_cookies) = (private_cookies, regular_cookies);

    // wipe no matter what
    (private_cookies, regular_cookies) = wipe_cookies(private_cookies, regular_cookies);

    let conn = &mut connection_pool.get()?;
    let user = db::attempt_login(conn, &login_req.username, &login_req.password)?;
    (private_cookies, regular_cookies) = user.cookies(private_cookies, regular_cookies);

    info!(id = user.id, username = user.username);

    return Ok((
        StatusCode::OK,
        private_cookies,
        regular_cookies,
        Json(LoginSuccess {
            username: user.username,
        }),
    ));
}

// TODO: remove session from database?
// TODO: better error logging
#[axum::debug_handler]
#[instrument(skip(private_cookies, regular_cookies))]
pub async fn logout(
    State(_): State<BackendState>, // for cookie jar key
    private_cookies: PrivateCookieJar,
    regular_cookies: CookieJar,
) -> impl IntoResponse {
    // for now, just tell client to wipe all cookies
    let (private_cookies, regular_cookies) = wipe_cookies(private_cookies, regular_cookies);
    info!("logged out");
    return (StatusCode::OK, private_cookies, regular_cookies);
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
    let user_id = match private_cookies.get(USER_ID_COOKIE) {
        Some(c) => c.value().to_string(),
        None => {
            warn!(e = "no id cookie");
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    let user_id = match user_id.parse::<i32>() {
        Ok(u) => u,
        Err(_e) => {
            warn!(e = "invalid id cookie", c = user_id);
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    let mut conn = match connection_pool.get() {
        Ok(c) => c,
        Err(e) => {
            error!("{:?}", e);
            return Err(StatusCode::INTERNAL_SERVER_ERROR);
        }
    };

    let u = db::get_user_by_id(&mut conn, user_id)?;

    info!(u = u.username);

    return Ok((
        StatusCode::OK,
        Json(WhoAmIResponse {
            username: u.username,
        }),
    ));
}
