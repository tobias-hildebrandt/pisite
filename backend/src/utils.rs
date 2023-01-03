pub fn relative_path(path: &str) -> String {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    return format!("{}{}{}", manifest_dir, "/", path);
}

pub fn setup_tracing() {
    // Configure a custom event formatter
    let format = tracing_subscriber::fmt::format()
        // .with_line_number(true)
        // .with_source_location(true)
        .with_target(true)

        .with_timer(tracing_subscriber::fmt::time::SystemTime)
        .compact();

    let my_subscriber = tracing_subscriber::fmt().event_format(format).finish();
    tracing::subscriber::set_global_default(my_subscriber).expect("setting tracing default failed");

    tracing::info!("tracing setup done");
}

pub fn api_route(prefix: &str, suffix: &str) -> String {
    format!("{}{}", prefix, suffix)
}
