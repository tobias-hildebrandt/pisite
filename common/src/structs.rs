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

pub static SESSION_COOKIE: &'static str = "session";
