use common::*;
use gloo_net::http::Request;
use yew::prelude::*;

pub struct NumberComponent {
    num: u64,
}

#[derive(Properties, PartialEq)]
pub struct NumberProps {
    pub endpoint: &'static str,
}

pub enum NumberMessage {
    Update,
    Set(u64),
    Reset,
}

impl Component for NumberComponent {
    type Message = NumberMessage;

    type Properties = NumberProps;

    fn create(_ctx: &Context<Self>) -> Self {
        Self { num: 0 }
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let on_click = ctx.link().callback(|_| NumberMessage::Update);
        html! {
            <button class="number" onclick={on_click}>
                {ctx.props().endpoint}{" = "}{self.num}
            </button>
        }
    }

    fn update(&mut self, ctx: &Context<Self>, message: Self::Message) -> bool {
        match message {
            NumberMessage::Update => {
                let ctx = ctx.clone();
                let e = ctx.props().endpoint;
                ctx.link().send_future(async {
                    let t1 = test_unwrap(e).await;
                    NumberMessage::Set(t1.number)
                });
                false // do not re-render yet
            }
            NumberMessage::Set(n) => {
                self.num = n;
                true // re-render
            }
            NumberMessage::Reset => {
                self.num = 0;
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
