use std::fmt::Display;

use serde::{Deserialize, Serialize};

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct Test1 {
    pub number: u64,
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct User {
    pub id: u64,
}

impl Display for User {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.id)
    }
}

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
pub enum LoginResponse {
    Error(LoginError),
    Success(LoginSuccess),
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum LogoutResponse {
    Error,
    Success,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct LoginSuccess {
    pub id: u64,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum LoginError {
    UsernameDoesNotExsist,
    PasswordIncorrect,
    InvalidData,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum PermissionFail {
    AuthenticationRequired,
    BadCookie,
}

pub static USER_ID_COOKIE: &'static str = "user_id";
pub static USERNAME_ID_COOKIE: &'static str = "username";
