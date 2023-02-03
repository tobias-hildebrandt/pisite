use serde::{Deserialize, Serialize};

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct Test1 {
    pub number: u64,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct RegisterRequest {
    pub username: String,
    pub register_key: String,
    pub password: String,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct LoginSuccess {
    pub username: String,
}

pub static USER_ID_COOKIE: &'static str = "user_id";
pub static USERNAME_ID_COOKIE: &'static str = "username";
