// we only need DB access for this executable
mod db;

use clap::Parser;

// take a simple argument
#[derive(clap::Parser)]
struct Args {
    #[arg(short = 'n', default_value_t = 10usize)]
    num_dummy: usize,
}

fn main() -> Result<(), anyhow::Error> {
    common::setup_tracing();

    let args = Args::parse();

    let pool = db::init_and_get_connection_pool()?;

    let mut conn = pool.get()?;

    db::create_dummy_users(&mut conn, args.num_dummy)?;

    Ok(())
}
