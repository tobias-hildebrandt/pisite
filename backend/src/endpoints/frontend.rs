use std::sync::Arc;

use axum::{
    extract::{Path, State},
    response::IntoResponse,
};
use hyper::{Body, Request, StatusCode};
use tower::Service;
use tower_http::services::ServeDir;
use tracing::{error, info, instrument};

pub struct FrontendState {
    pub serve_dir: tokio::sync::Mutex<ServeDir>,
}

// TODO: improve performance by allowing simulatenous reads
// TODO: sanitize input to avoid ../ or similar
// maybe switch to oneshot or cache files at launch?
#[instrument(skip_all)]
pub async fn frontend_handler(
    path: Option<Path<String>>, // option since we need to handle the root path
    State(frontend_state): State<Arc<FrontendState>>,
) -> impl IntoResponse {
    // handle serving from /
    let real_path = match path {
        Some(Path(path)) => {
            if path.eq("") || path.eq("/") {
                "/index.html".to_string()
            } else {
                format!("/{}", path)
            }
        }
        None => "/index.html".to_string(),
    };

    // create request to pass to tower_http's ServeDir
    let req = Request::builder()
        .uri(real_path)
        .body(Body::empty())
        .map_err(|e| {
            error!("Request::builder error: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // pass request to ServeDir service
    match frontend_state.serve_dir.lock().await.call(req).await {
        // will be a 404 if file not found
        Ok(res) => {
            if res.status().is_success() {
                info!(status = res.status().as_u16());
            }
            // non success will be caught by middleware layer

            return Ok(res);
        }
        Err(e) => {
            error!("ServeDir error: {}", e);
            return Err(StatusCode::NOT_FOUND);
        }
    }
}
