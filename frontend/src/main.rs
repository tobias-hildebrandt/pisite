use yew::prelude::*;
use tracing::{instrument, info};

mod auth;
mod number;

#[instrument]
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
    console_error_panic_hook::set_once();

    // TODO: set up custom tracing (without colors)
    tracing_wasm::set_as_global_default();

    info!("done setting up tracing");

    yew::start_app::<App>();
}
