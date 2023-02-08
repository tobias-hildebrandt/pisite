use axum::{
    extract::State,
    response::{ErrorResponse, IntoResponse},
    Json,
};
use axum_extra::extract::PrivateCookieJar;
use common::Test1;
use hyper::StatusCode;
use tracing::{info, instrument};

use crate::{cookies, db, endpoints::backend_state::BackendState};

#[axum::debug_handler]
#[instrument]
pub async fn api_test1() -> impl IntoResponse {
    let time = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    info!(time);
    return Json(Test1 { number: time });
}

#[axum::debug_handler]
#[instrument]
pub async fn api_test2() -> impl IntoResponse {
    let random = rand::random::<u64>();

    info!(random);

    return Json(Test1 { number: random });
}

#[axum::debug_handler]
#[instrument(skip(connection_pool, private_cookies))]
pub async fn api_test3(
    State(BackendState {
        key: _,
        connection_pool,
    }): State<BackendState>,
    private_cookies: PrivateCookieJar,
) -> Result<impl IntoResponse, ErrorResponse> {
    // verify user is authenticated
    let _u = cookies::user_from_cookies(private_cookies, &connection_pool)?;

    let mut connection = connection_pool.get()?;

    let users = db::get_all_users(&mut connection)?;

    let all_users_string = users
        .into_iter()
        .map(|u| format!("user({}, {})", u.id, u.username))
        .fold(String::new(), |mut accum, new| {
            accum.push_str(&new);
            accum.push_str(", ");
            accum
        });

    info!("success");

    let response = (StatusCode::OK, all_users_string).into_response();
    Ok(response)
}
