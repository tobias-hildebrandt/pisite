use axum::response::IntoResponse;
use diesel::connection::SimpleConnection;
use diesel::dsl::sql;
use diesel::prelude::*;
use diesel::r2d2::{ConnectionManager, Pool};
use diesel::{Connection, ConnectionResult, SqliteConnection};
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use hyper::StatusCode;
use r2d2::{self, PooledConnection};
use rand::Rng;
use tracing::{error, info, instrument, warn};

use super::crypt;
use super::schema;

const DEFAULT_DATABASE_LOCATION: &str = "relay.sqlite3";

const MIGRATIONS: EmbeddedMigrations = embed_migrations!("sql");

// error type returned for all DB operations
#[derive(thiserror::Error, Debug)]
pub enum DBError {
    #[error("DB Connection Error {0:?}")]
    Connection(#[from] ConnectionError),
    #[error("DB Migration Error {0:?}")]
    Migration(#[from] Box<dyn std::error::Error + Send + Sync>),
    #[error("DB Query Error {0:?}")]
    Query(#[from] diesel::result::Error),
    #[error("DB Pool Error {0:?}")]
    Pool(#[from] r2d2::Error),
    #[error("Crypt Error {0:?}")]
    Crypt(#[from] argon2::password_hash::Error),
}

impl IntoResponse for DBError {
    fn into_response(self) -> axum::response::Response {
        error!(target: "DBError", "{}", self);
        (StatusCode::INTERNAL_SERVER_ERROR).into_response()
    }
}

impl From<DBError> for hyper::StatusCode {
    fn from(val: DBError) -> Self {
        error!(target: "DBError", "{}", val);
        StatusCode::INTERNAL_SERVER_ERROR
    }
}

#[derive(Queryable, Debug)]
pub struct ExistingUser {
    pub id: i32,
    pub username: String,
    pub password_crypt: String,
}

#[derive(Insertable, Debug)]
#[diesel(table_name = schema::users)]
pub struct NewUser {
    pub username: String,
    pub password_crypt: String,
}

#[instrument(skip(connection, password_plaintext))]
fn create_dummy_user(
    connection: &mut SqliteConnection,
    username: &str,
    password_plaintext: &str,
) -> Result<(), DBError> {
    let crypted = crypt::encrypt_password(password_plaintext)?;
    let new_user = NewUser {
        username: username.to_string(),
        password_crypt: crypted,
    };
    diesel::insert_into(schema::users::table)
        .values(&new_user)
        .execute(connection)?;

    let resulting_user: ExistingUser = schema::users::dsl::users
        .find(sql("last_insert_rowid()"))
        .get_result(connection)?;

    info!("created user: {:?}", resulting_user);

    Ok(())
}

pub fn get_all_users(connection: &mut SqliteConnection) -> Result<Vec<ExistingUser>, DBError> {
    Ok(schema::users::dsl::users.load::<ExistingUser>(connection)?)
}

pub fn get_user(connection: &mut SqliteConnection, user_id: i32) -> Result<ExistingUser, DBError> {
    let u = schema::users::dsl::users
        .filter(schema::users::id.eq(user_id))
        .first(connection)?;
    Ok(u)
}

// private function, only used when initializing DB
fn direct_connection() -> ConnectionResult<SqliteConnection> {
    let url = if let Ok(env_var) = std::env::var("DATABASE_URL") {
        env_var
    } else {
        warn!(
            "no env var: DATABASE_URL, using default database location: {}",
            DEFAULT_DATABASE_LOCATION
        );
        DEFAULT_DATABASE_LOCATION.to_string()
    };
    SqliteConnection::establish(&url)
}

#[instrument(skip(connection))]
fn create_dummy_users(connection: &mut SqliteConnection, num: usize) {
    // create some dummy users
    for _ in 0..num {
        let num = rand::thread_rng().gen_range(0u16..100);
        let username = format!("testuser{:02}", num);
        let dummy_password = format!("dummy_pass_{:02}", num);
        if let Err(e) = create_dummy_user(connection, &username, &dummy_password) {
            error!("error adding user with username '{username}': {e}");
        }
    }
}

#[instrument]
fn init() -> Result<(), DBError> {
    // get initial connection
    let connection = &mut direct_connection()?;

    // run migrations if needed
    let _migrations_run: Vec<_> = connection
        .run_pending_migrations(MIGRATIONS)
        .map_err(DBError::Migration)?;

    // create_dummy_users(connection, 10);

    // load all users
    let users = schema::users::dsl::users.load::<ExistingUser>(connection)?;

    // print how many
    info!("got all {} users from DB", users.len());

    Ok(())
}

// wrapper struct for connection pool
#[derive(Clone)]
pub struct ConnPool {
    // private member, use get() to get a connection
    pool: Pool<ConnectionManager<SqliteConnection>>,
}

impl ConnPool {
    pub fn get(&self) -> Result<PooledConnection<ConnectionManager<SqliteConnection>>, DBError> {
        // TODO: figure out of PooledConnection is OK
        let conn = self.pool.get()?;

        Ok(conn)
    }
}

// https://stackoverflow.com/a/57717533
pub fn init_and_get_connection_pool() -> Result<ConnPool, DBError> {
    init()?;

    let pool = Pool::builder()
        .connection_customizer(Box::new(ConnOptions))
        .build(ConnectionManager::<SqliteConnection>::new(
            DEFAULT_DATABASE_LOCATION,
        ))?;

    Ok(ConnPool { pool })
}

#[derive(Debug)]
struct ConnOptions;

impl diesel::r2d2::CustomizeConnection<SqliteConnection, diesel::r2d2::Error> for ConnOptions {
    fn on_acquire(&self, conn: &mut SqliteConnection) -> Result<(), diesel::r2d2::Error> {
        // set up WAL
        conn.batch_execute("PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;")
            .map_err(diesel::r2d2::Error::QueryError)?;

        // set up busy timeout
        const TIMEOUT_SECONDS: f32 = 1.0;
        conn.batch_execute(&format!(
            "PRAGMA busy_timeout = {};",
            std::time::Duration::from_secs_f32(TIMEOUT_SECONDS).as_millis()
        ))
        .map_err(diesel::r2d2::Error::QueryError)?;

        Ok(())
    }
}
