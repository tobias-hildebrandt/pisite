use axum::response::IntoResponse;
use axum_extra::extract::{
    cookie::{Cookie, Expiration, SameSite},
    CookieJar, PrivateCookieJar,
};
use common::USER_ID_COOKIE;
use hyper::StatusCode;
use time::OffsetDateTime;
use tracing::warn;

use crate::db::{self, ExistingUser};

const COOKIE_DURATION: time::Duration = time::Duration::WEEK;

impl ExistingUser {
    pub fn apply_cookies(&self, private: PrivateCookieJar) -> PrivateCookieJar {
        // user id cookie
        let mut user_id_cookie = Cookie::new(USER_ID_COOKIE, self.id.to_string());

        // set path
        user_id_cookie.set_path("/"); // matches all subpaths

        // set expire
        let mut expiration = OffsetDateTime::now_utc();
        expiration += COOKIE_DURATION;
        user_id_cookie.set_expires(Expiration::from(Some(expiration)));

        // set same site security
        user_id_cookie.set_same_site(SameSite::Strict);

        // new private cookie jar, shadow old one
        let private = private.add(user_id_cookie);

        return private;
    }
}

pub fn get_wiped_cookie_jar() -> CookieJar {
    let regular = CookieJar::new();
    // add regular blank cookie that have already expired
    let mut user_id = Cookie::new(USER_ID_COOKIE, "");
    user_id.set_path("/"); // matches all subpaths
    user_id.set_expires(Expiration::from(OffsetDateTime::UNIX_EPOCH));

    let regular = regular.add(user_id);

    return regular;
}

#[derive(thiserror::Error, Debug)]
pub enum CookieAuthError {
    #[error("CookieAuthError NoId")]
    NoId,
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
            CookieAuthError::NoId => StatusCode::FORBIDDEN,
            CookieAuthError::NotI32 => StatusCode::UNAUTHORIZED,
            CookieAuthError::DBError(e) => e.into(),
        }
    }
}

pub fn user_from_cookies(
    private: PrivateCookieJar,
    connection_pool: &db::ConnPool,
) -> Result<ExistingUser, CookieAuthError> {
    // get user id cookie
    let user_id = private
        .get(USER_ID_COOKIE)
        .ok_or_else(|| CookieAuthError::NoId)?
        .value()
        .to_string();

    // parse user id cookie
    let user_id = user_id
        .parse::<i32>()
        .map_err(|_e| CookieAuthError::NotI32)?;

    // get database connection
    let mut conn = connection_pool.get()?;

    // get user from DB
    let u = db::get_user_by_id(&mut conn, user_id)?;

    Ok(u)
}
