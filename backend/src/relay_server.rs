#![allow(incomplete_features)]
#![feature(async_fn_in_trait)]

#[macro_use]
extern crate rocket;

#[macro_use]
mod utils;
mod auth;

use auth::Authenticated;
use common::*;
use rocket::{
    fs::FileServer,
    http::{Cookie, CookieJar, Status},
    serde::json::Json,
};

const API_PREFIX: &str = "/api/";

#[get("/test1")]
fn api_test1() -> Json<Test1> {
    let time = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    return Json(Test1 { number: time });
}

#[get("/test2")]
fn api_test2() -> Json<Test1> {
    let random = rand::random::<u64>();

    return Json(Test1 { number: random });
}

#[post("/login", data = "<login_req>")]
fn login(
    login_req: Option<Json<LoginRequest>>,
    cookie_jar: &CookieJar,
) -> (Status, Json<LoginResponse>) {
    // no body
    if login_req.is_none() {
        match cookie_jar.get_private(USER_ID_COOKIE) {
            Some(cookie) => {
                // you sent us a user ID cookie and no body
                let u = get_user_from_cookie(&cookie);
                println!("your user ID cookie: {}", cookie);

                match u {
                    Some(auth) => {
                        // wipe old cookie
                        wipe_cookies(cookie_jar);

                        // set your new cookies
                        auth.add_cookies_to(cookie_jar);
                    }
                    None => {
                        // your cookie is invalid
                        // wipe old cookie
                        wipe_cookies(cookie_jar);
                        return (
                            Status::Forbidden,
                            Json(LoginResponse::Error(LoginError::InvalidData)),
                        );
                    }
                }
            }
            None => {
                // no cookies and no body??
                eprintln!("no valid user_id cookie or body?");
                // delete any id cookie you have
                cookie_jar.remove_private(Cookie::named(USER_ID_COOKIE));
                return (
                    Status::BadRequest,
                    Json(LoginResponse::Error(LoginError::InvalidData)),
                );
            }
        }
    }
    // TODO: get from DB using login_req
    let user = Authenticated { id: 1 };
    let login_result = LoginResponse::Success(LoginSuccess { id: user.id });
    user.add_cookies_to(cookie_jar);

    return (Status::Ok, Json(login_result));
}

// TODO: use DB to check
fn get_user_from_cookie(cookie: &Cookie) -> Option<Authenticated> {
    return Some(Authenticated { id: 1 });
}

fn wipe_cookies(cookie_jar: &CookieJar) {
    cookie_jar.remove_private(Cookie::named(USER_ID_COOKIE));
    cookie_jar.remove(Cookie::named(USERNAME_ID_COOKIE));
}

#[post("/logout")]
fn logout(cookies: &CookieJar) -> Status {
    let cookie_opt = cookies.get_private(USER_ID_COOKIE);
    match cookie_opt {
        Some(c) => {
            println!("your cookie: {}", c);
            cookies.remove_private(c);
            Status::Ok
        }
        None => {
            // delete any id cookie you have
            cookies.remove_private(Cookie::named(USER_ID_COOKIE));
            Status::BadRequest
        }
    }
}

// #[catch(404)]
// fn general_not_found() -> Json<Error404> {
//     Json(Error404 {})
// }

#[launch]
fn rocket() -> _ {
    rocket::build()
        .mount(API_PREFIX, routes![api_test1, api_test2, login, logout])
        // .register(API_PREFIX, catchers![general_not_found])
        .mount(
            "/",
            FileServer::from(utils::relative_path("../frontend/dist")),
        )
}
