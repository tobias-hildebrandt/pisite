use axum::{extract::State, response::IntoResponse, Json};
use axum_extra::extract::{CookieJar, PrivateCookieJar};
use common::{LoginRequest, LoginSuccess};
use hyper::StatusCode;
use tracing::{info, instrument};

use crate::{
    cookies::{self, get_wiped_cookie_jar},
    db, BackendState,
};

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
    let (session, user) = match (|| {
        let conn = &mut connection_pool
            .get()
            .map_err(|e| hyper::StatusCode::from(e))?;

        let (session, user) = db::attempt_login(conn, &login_req.username, &login_req.password)
            .map_err(|e| hyper::StatusCode::from(e))?;

        Ok((session, user))
    })() {
        Ok((session, user)) => (session, user),
        Err(status) => {
            return Err((status, get_wiped_cookie_jar()));
        }
    };

    // success, add real cookies
    let private_cookies = session.apply_cookies(private_cookies);

    info!(id = user.id, username = user.username, session = session.id);

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
    let (_session, user) =
        cookies::session_and_user_from_cookies(private_cookies, &connection_pool)?;

    info!(u = user.username);

    return Ok((
        StatusCode::OK,
        Json(LoginSuccess {
            username: user.username,
        }),
    ));
}
