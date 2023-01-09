use yew::prelude::*;

mod auth;
mod number;
#[macro_use]
mod utils;

#[function_component(App)]
fn app() -> Html {
    html! {
        <>
            <h1>{"Hello World"}</h1>
            // each html attribute corresponds to a value in the props argument
            <auth::auth::AuthComponent /><br />
            <number::NumberComponent endpoint="/api/test1"/><br />
            <number::NumberComponent endpoint="/api/test2"/><br />
        </>
    }
}

fn main() {
    yew::start_app::<App>();
}
