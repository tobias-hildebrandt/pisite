use axum_extra::extract::{PrivateCookieJar, CookieJar, cookie::Cookie};
use common::{USER_ID_COOKIE, USERNAME_ID_COOKIE};

pub struct Authenticated {
    pub id: u64,
}

impl Authenticated {
    pub fn cookies(&self, private: PrivateCookieJar, regular: CookieJar) -> (PrivateCookieJar, CookieJar) {
        let username = "this_is_a_username";
        let private = private.add(Cookie::new(USER_ID_COOKIE, self.id.to_string()));
        let regular = regular.add(Cookie::new(USERNAME_ID_COOKIE, username));

        return (private, regular);
    }
}
