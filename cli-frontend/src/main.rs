use std::{path::PathBuf, str::FromStr, sync::Arc};

use clap::Parser;
use config::Config;

mod config;

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    let args = config::Arguments::parse();

    println!("args: {:#?}", args);

    let config = args.get_config()?;

    let mut initial_cookies = reqwest_cookie_store::CookieStore::default();

    // TODO: add token if specified
    // if let (Some(token), Some(url)) = (config.token, config.url) {
    //     cookie::Cookie::from_str(s)
    //     let raw_cookie = cookie::Cookie::build(common::USER_ID_COOKIE, token)
    //         .domain(url.clone())
    //         .path("/")
    //         .secure(true)
    //         .http_only(true)
    //         .finish();
    //     let c = cookie_store::Cookie::try_from_raw_cookie(&raw_cookie, &(&url.parse()?))?;

    //     initial_cookies.insert(c, &url.parse::<reqwest::Url>()?)?;
    // }

    let cookies = reqwest_cookie_store::CookieStoreMutex::new(initial_cookies);
    let cookies = Arc::new(cookies);

    let req_client = reqwest::Client::builder()
        .cookie_store(true)
        .cookie_provider(cookies.clone())
        .build()?;

    let mut client = Client {
        save_file: args.config_file,
        cookies,
        req_client,
    };

    match args.command {
        config::Command::Login { username } => {
            client.login().await?;
        }
        _ => todo!(),
    }

    Ok(())
}

struct Client {
    save_file: Option<PathBuf>,
    cookies: Arc<reqwest_cookie_store::CookieStoreMutex>,
    req_client: reqwest::Client,
}

impl Client {
    async fn login(&mut self) -> Result<(), anyhow::Error> {
        let response = self
            .req_client
            .post("http://localhost:8000/api/login")
            .header("Content-type", "application/json")
            .body(
                r#"{
                    "username": "test_user",
                    "password": "test_password"
                }"#,
            )
            .send()
            .await?;

        println!("response: {}", response.text().await?.as_str());

        let s = {
            let mut buffer = Box::new(Vec::new());
            let cookies = self.cookies.lock().unwrap();

            cookies
                .save_json(&mut buffer)
                .map_err(|e| anyhow::anyhow!(e))?;
            std::str::from_utf8(buffer.as_slice()).unwrap().to_string()
        };
        println!("cookies: {:?}", s);

        Ok(())
    }
}
