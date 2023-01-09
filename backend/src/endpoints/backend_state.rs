use axum::extract::FromRef;
use axum_extra::extract::cookie::Key;

use crate::db;

#[derive(Clone)]
pub struct BackendState {
    // private cookie key
    pub key: Key,
    // arc mutex for the database connection
    // (sqlite does not support multiple writers)
    pub connection_pool: db::ConnPool,
}

// so our signed cookie jar can get the key from the backend state
impl FromRef<BackendState> for Key {
    fn from_ref(state: &BackendState) -> Self {
        state.key.clone()
    }
}
