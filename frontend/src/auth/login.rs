use common::LoginRequest;
use gloo_net::http::{Method, Request};
use wasm_bindgen::JsCast;
use web_sys::{Event, FocusEvent, HtmlInputElement};
use yew::{html, Callback, Component, Context, Html, Properties};

use crate::console_log;

use super::auth::LoginResponse;

/// Component that allows login.
/// Displays form and login button.
#[derive(PartialEq, Clone, Default)]
pub struct LoginComponent {
    username: String,
    password: String,
}

/// Properties for LoginComponent
#[derive(Properties, PartialEq)]
pub struct LoginProps {
    pub parent_callback: Callback<LoginResponse>,
}

pub enum LoginMessage {
    UserInputSubmit,
    AskWithCookie,
    GotResponse(LoginResponse),
    UserInputUsernameChange(String),
    UserInputPasswordChange(String),
    Failure(gloo_net::Error),
}

impl Component for LoginComponent {
    type Message = LoginMessage;

    type Properties = LoginProps;

    fn create(ctx: &Context<Self>) -> Self {
        // check if we are already logged in (via cookie) on creation
        ctx.link().send_message(LoginMessage::AskWithCookie);

        Self::default()
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let on_username_change = ctx.link().callback(|event: Event| {
            let input = event
                .target()
                .unwrap()
                .unchecked_into::<HtmlInputElement>()
                .value();
            LoginMessage::UserInputUsernameChange(input)
        });

        let on_password_change = ctx.link().callback(|event: Event| {
            let input = event
                .target()
                .unwrap()
                .unchecked_into::<HtmlInputElement>()
                .value();
            LoginMessage::UserInputPasswordChange(input)
        });

        let on_submit = ctx.link().callback(|e: FocusEvent| {
            e.prevent_default();
            LoginMessage::UserInputSubmit
        });

        html! {
            <>
                {"Log in"}
                <form onsubmit={on_submit}>
                    <label for="username">{"Username"}</label><br />
                    <input type="text" id="username" name="username" onchange={on_username_change}/><br />
                    <label for="password">{"Password"}</label><br />
                    <input type="password" id="password" name="password" onchange={on_password_change}/><br />
                    <input type="submit" value="Log in" />
                </form>
            </>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, message: Self::Message) -> bool {
        match message {
            LoginMessage::UserInputSubmit => {
                // try to log in
                let req = LoginRequest {
                    username: self.username.clone(),
                    password: self.password.clone(),
                };

                ctx.link().send_future(async {
                    match try_login(req).await {
                        Ok(r) => LoginMessage::GotResponse(r),
                        Err(e) => LoginMessage::Failure(e),
                    }
                });

                false
            }
            LoginMessage::GotResponse(r) => {
                ctx.props().parent_callback.emit(r);
                false
            }
            LoginMessage::UserInputUsernameChange(u) => {
                self.username = u;
                false
            }
            LoginMessage::UserInputPasswordChange(p) => {
                self.password = p;
                false
            }
            LoginMessage::Failure(e) => {
                console_log!("login error: {}", e);

                false
            }
            LoginMessage::AskWithCookie => {
                ctx.link().send_future(async {
                    match ask_with_cookie().await {
                        Ok(r) => LoginMessage::GotResponse(r),
                        Err(e) => LoginMessage::Failure(e),
                    }
                });

                true
            }
        }
    }
}

async fn try_login(req: LoginRequest) -> Result<LoginResponse, gloo_net::Error> {
    let response = Request::new("/api/login")
        .method(Method::POST)
        .body(serde_json::to_string(&req).unwrap())
        .header("Content-Type", "application/json;charset=UTF-8")
        .send()
        .await?;

    // anything but 200 is a failure
    if response.status() != 200 {
        return Ok(LoginResponse::Failure);
    }

    let parsed = response.json().await?;

    Ok(LoginResponse::Success(parsed))
}

async fn ask_with_cookie() -> Result<LoginResponse, gloo_net::Error> {
    let response = Request::new("/api/whoami")
        .method(Method::POST)
        .send()
        .await?;

    // anything but 200 is a failure
    if response.status() != 200 {
        return Ok(LoginResponse::Failure);
    }

    let parsed = response.json().await?;

    Ok(LoginResponse::Success(parsed))
}
