use std::fmt::Display;

use common::LoginSuccess;
use tracing::{info, instrument};
use yew::{html, Component, Context, Html};

use super::login::LoginComponent;
use super::logout::LogoutComponent;

/// Component that allows login and logout.
/// Displays login status.
#[derive(PartialEq, Clone, Default)]
pub struct AuthComponent {
    status: AuthStatus,
}

/// Respresents the current login status.
#[derive(PartialEq, Clone)]
pub enum AuthStatus {
    LoggedIn(LoginSuccess),
    LoggedOut,
}

impl Display for AuthStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuthStatus::LoggedIn(success) => write!(f, "Logged In: {}", success.username),
            AuthStatus::LoggedOut => write!(f, "Logged Out"),
        }
    }
}

impl Default for AuthStatus {
    fn default() -> Self {
        Self::LoggedOut
    }
}

/// Internal message for AuthComponent
#[derive(Debug)]
pub enum AuthComponentMessage {
    /// Result of a login attempt.
    /// Sent by a child component via callback.
    Login(LoginResponse),
    /// Result of a logout attempt.
    /// Sent by a child component via callback.
    Logout(LogoutResponse),
}

/// Abstraction of response to a login request.
#[derive(Debug)]
pub enum LoginResponse {
    Success(LoginSuccess),
    Failure,
}

/// Abstraction of response to a logout request.
#[derive(Debug)]
pub enum LogoutResponse {
    Success,
    Failure,
}

impl Component for AuthComponent {
    type Message = AuthComponentMessage;

    type Properties = ();

    #[instrument(skip_all)]
    fn create(_ctx: &Context<Self>) -> Self {
        info!("");
        Self::default()
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        // callbacks invoked by child components (send a message to this component)
        let login_cb = ctx
            .link()
            .callback(|result: LoginResponse| AuthComponentMessage::Login(result));

        let logout_cb = ctx.link().callback(|m| AuthComponentMessage::Logout(m));

        html! {
            <>
            <div id="login_status">{"Status: "}{&self.status}</div>
            if let AuthStatus::LoggedIn(_) = &self.status {
                <LogoutComponent parent_callback={logout_cb} />
            } else {
                <LoginComponent parent_callback={login_cb} />
            }
            </>
        }
    }

    #[instrument(skip(self, _ctx))]
    fn update(&mut self, _ctx: &Context<Self>, msg: Self::Message) -> bool {
        match msg {
            AuthComponentMessage::Login(response) => match response {
                LoginResponse::Failure => {
                    info!("AuthComponent Login Failure");

                    false
                }
                LoginResponse::Success(s) => {
                    info!("AuthComponent Login: {}", s.username);

                    self.status = AuthStatus::LoggedIn(s);

                    true
                }
            },
            AuthComponentMessage::Logout(m) => match m {
                LogoutResponse::Success => {
                    self.status = AuthStatus::LoggedOut;
                    true
                }
                LogoutResponse::Failure => false,
            },
        }
    }
}
