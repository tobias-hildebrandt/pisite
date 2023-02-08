use common::*;
use gloo_net::http::Request;
use yew::prelude::*;

/// Component that displays a number endpoint.
/// Displays button with status.
pub struct NumberComponent {
    num: u64,
}

/// Properties for NumberComponent
#[derive(Properties, PartialEq)]
pub struct NumberProps {
    pub endpoint: &'static str,
}

/// Internal message for NumberComponent.
pub enum NumberComponentMessage {
    /// Sent to trigger an update.
    Update,
    /// Sent when the number should be updated.
    Set(u64),
}

impl Component for NumberComponent {
    type Message = NumberComponentMessage;

    type Properties = NumberProps;

    fn create(_ctx: &Context<Self>) -> Self {
        Self { num: 0 }
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let on_click = ctx.link().callback(|_| NumberComponentMessage::Update);
        html! {
            <button class="number" onclick={on_click}>
                {ctx.props().endpoint}{" = "}{self.num}
            </button>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, message: Self::Message) -> bool {
        match message {
            NumberComponentMessage::Update => {
                let ctx = ctx.clone();
                let e = ctx.props().endpoint;
                ctx.link().send_future(async {
                    let t1 = test_unwrap(e).await;
                    NumberComponentMessage::Set(t1.number)
                });
                false // do not re-render yet
            }
            NumberComponentMessage::Set(n) => {
                self.num = n;
                true // re-render
            }
        }
    }
}

async fn test_unwrap(endpoint: &'static str) -> Test1 {
    Request::new(endpoint)
        .send()
        .await
        .unwrap()
        .json()
        .await
        .unwrap()
}
