use gloo_net::http::{Method, Request};

use yew::{html, Callback, Component, Context, Html, Properties};

use crate::console_log;

use super::auth::LogoutResponse;

/// Component that allows logout.
/// Shows button that triggers a logout.
pub struct LogoutComponent;

/// Properties for LogoutComponent
#[derive(Properties, PartialEq)]
pub struct LogoutProperties {
    /// Called to inform parent of result of an logout attempt
    pub parent_callback: Callback<LogoutResponse>,
}

/// Internal message for LogoutComponent.
pub enum LogoutComponentMessage {
    /// Sent to trigger a logout attempt
    DoLogout,
    /// Sent in response to a logout attempt
    Result { success: bool },
}

impl Component for LogoutComponent {
    type Message = LogoutComponentMessage;

    type Properties = LogoutProperties;

    fn create(_ctx: &Context<Self>) -> Self {
        Self
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let click = ctx.link().callback(|_| LogoutComponentMessage::DoLogout);
        html! {
            <button id="logout_button" onclick={click}>{"Logout"}</button>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, msg: Self::Message) -> bool {
        match msg {
            LogoutComponentMessage::Result { success } => {
                console_log!("LogoutComponent: logout result: {}", success);
                ctx.props().parent_callback.emit(match success {
                    true => LogoutResponse::Success,
                    false => LogoutResponse::Failure,
                });
            }
            LogoutComponentMessage::DoLogout => {
                ctx.link().send_future(async {
                    let result = try_logout().await;
                    match result {
                        Ok(success) => LogoutComponentMessage::Result { success },
                        Err(e) => {
                            console_log!("LogoutComponent: logout failure: {}", e);
                            LogoutComponentMessage::Result { success: false }
                        }
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
