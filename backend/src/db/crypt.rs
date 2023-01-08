use argon2::{password_hash::{SaltString, self}, Argon2, PasswordHasher, PasswordHash, PasswordVerifier};
use rand::rngs::OsRng;

pub fn encrypt_password(plaintext: &str) -> Result<String, password_hash::Error> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    // output includes salt
    let hashed_and_salt = argon2.hash_password(plaintext.as_bytes(), &salt)?.to_string();

    Ok(hashed_and_salt)
}

pub fn verify_password(plaintext: &str, hashed: &str) -> Result<bool, password_hash::Error> {
    // hashed includes the salt
    let parsed_hash = PasswordHash::new(hashed)?;
    let argon2 = Argon2::default();
    Ok(argon2.verify_password(plaintext.as_bytes(), &parsed_hash).is_ok())
}
