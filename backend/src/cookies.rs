use axum_extra::extract::{
    cookie::{Cookie, Expiration},
    CookieJar, PrivateCookieJar,
};
use common::{USERNAME_ID_COOKIE, USER_ID_COOKIE};
use time::OffsetDateTime;

use crate::db::ExistingUser;

impl ExistingUser {
    pub fn cookies(
        &self,
        private: PrivateCookieJar,
        regular: CookieJar,
    ) -> (PrivateCookieJar, CookieJar) {
        // TODO: harden cookies
        // user id cookie
        let mut user_id_cookie = Cookie::new(USER_ID_COOKIE, self.id.to_string());
        user_id_cookie.set_path("/"); // matches all subpaths

        // new private cookie jar
        let private = private.add(user_id_cookie);

        return (private, regular);
    }
}

pub fn wipe_cookies(
    private: PrivateCookieJar,
    regular: CookieJar,
) -> (PrivateCookieJar, CookieJar) {
    // remove old cookies
    let private = private.remove(Cookie::named(USER_ID_COOKIE));
    let regular = regular.remove(Cookie::named(USERNAME_ID_COOKIE));

    // add regular blank cookies that have already expired
    let mut user_id = Cookie::new(USER_ID_COOKIE, "");
    user_id.set_path("/"); // matches all subpaths
    user_id.set_expires(Expiration::from(OffsetDateTime::UNIX_EPOCH));

    let regular = regular.add(user_id);
    // let regular = regular.add(username);

    return (private, regular);
}
