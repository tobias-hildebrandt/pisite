use axum::response::IntoResponse;
use axum_extra::extract::{
    cookie::{Cookie, Expiration, SameSite},
    CookieJar, PrivateCookieJar,
};
use common::SESSION_COOKIE;
use hyper::StatusCode;
use time::OffsetDateTime;
use tracing::warn;

use crate::db::{self, ExistingLoginSession, ExistingUser};

const COOKIE_DURATION: time::Duration = time::Duration::WEEK;

impl ExistingLoginSession {
    pub fn apply_cookies(&self, private: PrivateCookieJar) -> PrivateCookieJar {
        // user id cookie
        let mut session_cookie = Cookie::new(SESSION_COOKIE, self.id.to_string());

        // set path
        session_cookie.set_path("/"); // matches all subpaths

        // set expire
        let mut expiration = OffsetDateTime::now_utc();
        expiration += COOKIE_DURATION;
        session_cookie.set_expires(Expiration::from(Some(expiration)));

        set_cookie_security(&mut session_cookie);

        // new private cookie jar, shadow old one
        let private = private.add(session_cookie);

        return private;
    }
}

pub fn get_wiped_cookie_jar() -> CookieJar {
    let regular = CookieJar::new();
    // add regular blank cookie that have already expired
    let mut session_cookie = Cookie::new(SESSION_COOKIE, "");
    session_cookie.set_path("/"); // matches all subpaths
    session_cookie.set_expires(Expiration::from(OffsetDateTime::UNIX_EPOCH));

    set_cookie_security(&mut session_cookie);

    let regular = regular.add(session_cookie);

    return regular;
}

fn set_cookie_security(cookie: &mut Cookie) {
    // set same site security
    cookie.set_same_site(SameSite::Strict);

    // http only
    cookie.set_http_only(true);

    // secure, tell browser to only allow on https (or localhost)
    cookie.set_secure(true);
}

#[derive(thiserror::Error, Debug)]
pub enum CookieAuthError {
    #[error("CookieAuthError NoId")]
    NoSessionCookie,
    #[error("CookieAuthError NotI32")]
    NotI32,
    #[error("CookieAuthError DBError: {0:?}")]
    DBError(#[from] db::DBError),
}

impl IntoResponse for CookieAuthError {
    fn into_response(self) -> axum::response::Response {
        let code = hyper::StatusCode::from(self);
        code.into_response()
    }
}

impl From<CookieAuthError> for hyper::StatusCode {
    fn from(val: CookieAuthError) -> Self {
        warn!("{}", val);

        match val {
            CookieAuthError::NoSessionCookie => StatusCode::FORBIDDEN,
            CookieAuthError::NotI32 => StatusCode::UNAUTHORIZED,
            CookieAuthError::DBError(e) => e.into(),
        }
    }
}

pub fn session_and_user_from_cookies(
    private: PrivateCookieJar,
    connection_pool: &db::ConnPool,
) -> Result<(ExistingLoginSession, ExistingUser), CookieAuthError> {
    // get session id cookie
    let session_id_str = private
        .get(SESSION_COOKIE)
        .ok_or_else(|| CookieAuthError::NoSessionCookie)?
        .value()
        .to_string();

    // parse session id cookie
    let session_id = session_id_str
        .parse::<i32>()
        .map_err(|_e| CookieAuthError::NotI32)?;

    // get database connection
    let mut conn = connection_pool.get()?;

    // get session and user from DB
    let sess_and_user = db::get_session(&mut conn, session_id)?;

    Ok(sess_and_user)
}
