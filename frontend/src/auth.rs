use std::fmt::Display;

use crate::console_log;

use common::*;
use gloo_net::http::Method;
use gloo_net::http::Request;
use wasm_bindgen::JsCast;
use web_sys::HtmlInputElement;
use yew::prelude::*;
use yew::{Component, Context, Html, TargetCast};

#[derive(PartialEq, Clone)]
pub struct AuthComponent {
    status: AuthStatus,
}

#[derive(PartialEq, Clone)]
pub enum AuthStatus {
    LoggedIn(User),
    LoggedOut,
}

impl Display for AuthStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuthStatus::LoggedIn(user) => write!(f, "Logged In: {}", user),
            AuthStatus::LoggedOut => write!(f, "Logged Out"),
        }
    }
}

pub enum AuthMessage {
    LoginMessage(LoginResponse),
    LogoutMessage(LogoutResponse),
}

impl Component for AuthComponent {
    type Message = AuthMessage;

    type Properties = ();

    fn create(_ctx: &Context<Self>) -> Self {
        AuthComponent {
            status: AuthStatus::LoggedOut,
        }
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let login_cb = ctx
            .link()
            .callback(|result: LoginResponse| AuthMessage::LoginMessage(result));

        let logout_cb = ctx.link().callback(|m| AuthMessage::LogoutMessage(m));

        html! {
            <>
            <div id="login_status">{"Status: "}{&self.status}</div>
            if let AuthStatus::LoggedIn(_) = &self.status {
                <LogoutComponent callback={logout_cb} />
            } else {
                <LoginComponent callback={login_cb} />
            }
            </>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, msg: Self::Message) -> bool {
        match msg {
            AuthMessage::LoginMessage(response) => match response {
                LoginResponse::Error(e) => {
                    unsafe {
                        console_log!("{:#?}", e);
                    }
                    false
                }
                LoginResponse::Success(s) => {
                    self.status = AuthStatus::LoggedIn(User { username: s.username });
                    true
                }
            },
            AuthMessage::LogoutMessage(m) => match m {
                LogoutResponse::Error => false,
                LogoutResponse::Success => {
                    self.status = AuthStatus::LoggedOut;
                    true
                }
            },
        }
    }
}

#[derive(PartialEq, Clone)]
pub struct LoginComponent {
    username: String,
    password: String,
}

#[derive(Properties, PartialEq)]
pub struct LoginProps {
    callback: Callback<LoginResponse>,
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
        // see if we are already logged in
        // ctx.link().send_message(LoginMessage::AskWithCookie);

        Self {
            username: "".to_string(),
            password: "".to_string(),
        }
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
                ctx.props().callback.emit(r);
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
                unsafe {
                    console_log!("login error: {}", e);
                }
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

    let parsed = response.json().await?;

    Ok(parsed)
}

async fn ask_with_cookie() -> Result<LoginResponse, gloo_net::Error> {
    let response = Request::new("/api/login")
        .method(Method::POST)
        .send()
        .await?;

    let parsed = response.json().await?;

    Ok(parsed)
}

pub struct LogoutComponent;

#[derive(Properties, PartialEq)]
pub struct LogoutProperties {
    callback: Callback<LogoutResponse>,
}

pub enum LogoutMessage {
    Success,
    Failure,
    Attempt,
}

impl Component for LogoutComponent {
    type Message = LogoutMessage;

    type Properties = LogoutProperties;

    fn create(ctx: &Context<Self>) -> Self {
        Self
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let click = ctx.link().callback(|_| LogoutMessage::Attempt);
        html! {
            <button id="logout_button" onclick={click}>{"Logout"}</button>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, msg: Self::Message) -> bool {
        match msg {
            LogoutMessage::Success => {
                ctx.props().callback.emit(LogoutResponse::Success);
            }
            LogoutMessage::Failure => {
                ctx.props().callback.emit(LogoutResponse::Error);
            }
            LogoutMessage::Attempt => {
                ctx.link().send_future(async {
                    let r = try_logout().await;
                    match r {
                        Ok(e) => {
                            if e {
                                LogoutMessage::Success
                            } else {
                                LogoutMessage::Failure
                            }
                        }
                        Err(e) => LogoutMessage::Failure,
                    }
                });
            }
        }

        true
    }
}

async fn try_logout() -> Result<bool, gloo_net::Error> {
    let response = Request::new("/api/logout")
        .method(Method::POST)
        .send()
        .await?;

    Ok(response.status() == 200)
}
