pub fn relative_path(path: &str) -> String {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    return format!("{}{}{}", manifest_dir, "/", path);
}
