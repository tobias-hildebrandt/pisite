use axum_extra::extract::{PrivateCookieJar, CookieJar, cookie::Cookie};
use common::{USER_ID_COOKIE, USERNAME_ID_COOKIE};

use crate::db::ExistingUser;

impl ExistingUser {
    pub fn cookies(&self, private: PrivateCookieJar, regular: CookieJar) -> (PrivateCookieJar, CookieJar) {
        // TODO: harden cookies
        let username = "this_is_a_username";

        // user id cookie
        let mut user_id_cookie = Cookie::new(USER_ID_COOKIE, self.id.to_string());
        user_id_cookie.set_path("/"); // matches all subpaths

        // new private cookie jar
        let private = private.add(user_id_cookie);

        // let mut username_cookie = Cookie::new(USERNAME_ID_COOKIE, username);
        // username_cookie.set_path("/");

        // let regular = regular.add(username_cookie);

        return (private, regular);
    }
}
