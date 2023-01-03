use common::*;
use rocket::http::{Cookie, CookieJar, Status};
use rocket::outcome::Outcome;
use rocket::request::FromRequest;

pub struct Authenticated {
    pub id: u64,
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for Authenticated {
    type Error = PermissionFail;

    async fn from_request(
        request: &'r rocket::Request<'_>,
    ) -> rocket::request::Outcome<Self, Self::Error> {
        match request.cookies().get_private(USER_ID_COOKIE) {
            Some(value) => match value.value().parse::<u64>() {
                Ok(val) => Outcome::Success(Authenticated { id: val }),
                Err(_) => Outcome::Failure((Status::BadRequest, PermissionFail::BadCookie)),
            },
            None => Outcome::Failure((Status::Forbidden, PermissionFail::AuthenticationRequired)),
        }
    }
}

impl From<Authenticated> for LoginSuccess {
    fn from(u: Authenticated) -> Self {
        LoginSuccess { id: u.id }
    }
}

impl Authenticated {
    pub fn add_cookies_to(&self, cookie_jar: &CookieJar) {
        let username = "this_is_a_username";
        cookie_jar.add_private(Cookie::new(USER_ID_COOKIE, self.id.to_string()));
        cookie_jar.add(Cookie::new(USERNAME_ID_COOKIE, username));
    }
}
