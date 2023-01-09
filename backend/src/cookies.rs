use axum_extra::extract::{
    cookie::{Cookie, Expiration, SameSite},
    CookieJar, PrivateCookieJar,
};
use common::USER_ID_COOKIE;
use time::OffsetDateTime;

use crate::db::ExistingUser;

const COOKIE_DURATION: time::Duration = time::Duration::WEEK;

impl ExistingUser {
    pub fn cookies(&self, private: PrivateCookieJar) -> PrivateCookieJar {
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
