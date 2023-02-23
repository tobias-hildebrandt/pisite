use std::ops::Add;

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
use tracing::{error, info, instrument, span, warn};

use crate::db::crypt;

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
        let code = hyper::StatusCode::from(self);
        code.into_response()
    }
}

impl From<DBError> for hyper::StatusCode {
    fn from(val: DBError) -> Self {
        warn!("{}", val);

        match val {
            DBError::Query(_) => StatusCode::UNAUTHORIZED,
            DBError::Connection(_)
            | DBError::Migration(_)
            | DBError::Pool(_)
            | DBError::Crypt(_) => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}

#[derive(Insertable, Debug)]
#[diesel(table_name = schema::login_sessions)]
pub struct NewLoginSession {
    pub user_id: i32,
    pub expiration: time::PrimitiveDateTime,
}

#[derive(Queryable, Debug)]
pub struct ExistingLoginSession {
    pub id: i32,
    pub user_id: i32,
    pub expiry: time::PrimitiveDateTime,
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

pub fn get_session(
    connection: &mut SqliteConnection,
    id: i32,
) -> Result<(ExistingLoginSession, ExistingUser), DBError> {
    // wipe_expired_sessions(connection)?;

    let now_utc = time::OffsetDateTime::now_utc();
    let now_primitive = time::PrimitiveDateTime::new(now_utc.date(), now_utc.time());

    let session: ExistingLoginSession = schema::login_sessions::dsl::login_sessions
        .filter(schema::login_sessions::id.eq(id)) // correct user
        .filter(schema::login_sessions::expiration.gt(now_primitive)) // and not yet expired
        .first(connection)?;

    let user = get_user_by_id(connection, session.user_id)?;

    Ok((session, user))
}

// TODO: decide whether to actually wipe sessions or not
#[allow(unused)]
fn wipe_expired_sessions(connection: &mut SqliteConnection) -> Result<(), DBError> {
    // get current time
    let now_utc = time::OffsetDateTime::now_utc();
    let now_primitive = time::PrimitiveDateTime::new(now_utc.date(), now_utc.time());

    // find all sessions that expired before current time
    let expired = schema::login_sessions::dsl::login_sessions
        .filter(schema::login_sessions::expiration.lt(now_primitive));

    // delete
    let deletion = diesel::delete(expired);

    // execute
    deletion.execute(connection)?;

    Ok(())
}

pub fn get_all_users(connection: &mut SqliteConnection) -> Result<Vec<ExistingUser>, DBError> {
    Ok(schema::users::dsl::users.load::<ExistingUser>(connection)?)
}

pub fn get_user_by_id(
    connection: &mut SqliteConnection,
    user_id: i32,
) -> Result<ExistingUser, DBError> {
    let u = schema::users::dsl::users
        .filter(schema::users::id.eq(user_id))
        .first(connection)?;
    Ok(u)
}

pub fn get_user_by_username(
    connection: &mut SqliteConnection,
    username: &str,
) -> Result<ExistingUser, DBError> {
    let u = schema::users::dsl::users
        .filter(schema::users::username.eq(username))
        .first(connection)?;

    Ok(u)
}

#[derive(thiserror::Error, Debug)]
pub enum LoginError {
    #[error("DB Error {0:?}")]
    DBError(#[from] DBError),
    #[error("Login Fail")]
    LoginFail,
}

impl From<LoginError> for hyper::StatusCode {
    fn from(val: LoginError) -> Self {
        let _enter = span!(tracing::Level::WARN, "LoginError").entered();
        match val {
            LoginError::LoginFail => StatusCode::UNAUTHORIZED,
            LoginError::DBError(e) => e.into(),
        }
    }
}

pub fn attempt_login(
    connection: &mut SqliteConnection,
    username: &str,
    password_plaintext: &str,
) -> Result<(ExistingLoginSession, ExistingUser), LoginError> {
    let u: ExistingUser = schema::users::dsl::users
        .filter(schema::users::username.eq(username))
        .first(connection)
        .map_err(|e| LoginError::DBError(DBError::Query(e)))?;

    let valid_login = crypt::verify_password(password_plaintext, &u.password_crypt)
        .map_err(|e| LoginError::DBError(DBError::Crypt(e)))?;

    if !valid_login {
        return Err(LoginError::LoginFail);
    }

    let now = time::OffsetDateTime::now_utc();

    let expiry_utc = now.add(time::Duration::WEEK);

    let session = NewLoginSession {
        user_id: u.id,
        expiration: time::PrimitiveDateTime::new(expiry_utc.date(), expiry_utc.time()),
    };

    diesel::insert_into(schema::login_sessions::table)
        .values(&session)
        .execute(connection)
        .map_err(|e| LoginError::DBError(DBError::Query(e)))?;

    // can't join becauseof last_insert_rowid()?
    let resulting_session: ExistingLoginSession = schema::login_sessions::dsl::login_sessions
        .find(sql("last_insert_rowid()"))
        .first(connection)
        .map_err(|e| LoginError::DBError(DBError::Query(e)))?;

    let user: ExistingUser = get_user_by_id(connection, resulting_session.user_id)?;

    Ok((resulting_session, user))
}

fn database_location() -> String {
    if let Ok(env_var) = std::env::var("DATABASE_URL") {
        info!("using data base location: {}", env_var);
        env_var
    } else {
        warn!(
            "no env var: DATABASE_URL, using default database location: {}",
            DEFAULT_DATABASE_LOCATION
        );
        DEFAULT_DATABASE_LOCATION.to_string()
    }
}

// private function, only used when initializing DB
fn direct_connection(database_location: &str) -> ConnectionResult<SqliteConnection> {
    SqliteConnection::establish(&database_location)
}

#[instrument(skip(connection))]
pub fn create_dummy_users(
    connection: &mut SqliteConnection,
    num: usize,
) -> Result<(), ConnectionError> {
    // create some dummy users
    for _ in 0..num {
        let num = rand::thread_rng().gen_range(0u16..100);
        let username = format!("testuser{:02}", num);
        let dummy_password = format!("dummy_pass_{:02}", num);
        if let Err(e) = create_dummy_user(connection, &username, &dummy_password) {
            error!("error adding user with username '{username}': {e}");
        }
    }

    Ok(())
}

fn create_test_user(connection: &mut SqliteConnection) -> Result<(), DBError> {
    const TEST_USERNAME: &str = "test_user";
    const TEST_PLAIN_PASS: &str = "test_password";
    match get_user_by_username(connection, TEST_USERNAME) {
        Ok(u) => {
            info!("test user already exists: {:?}", u);
            Ok(())
        }
        Err(e) => match e {
            DBError::Query(_q) => create_dummy_user(connection, TEST_USERNAME, TEST_PLAIN_PASS),
            DBError::Connection(_) | _ => {
                error!("{:?}", e);
                Err(e)
            }
        },
    }
}

#[instrument(skip_all)]
fn init(database_location: &str) -> Result<(), DBError> {
    // get initial connection
    let connection = &mut direct_connection(database_location)?;

    // run migrations if needed
    let _migrations_run: Vec<_> = connection
        .run_pending_migrations(MIGRATIONS)
        .map_err(DBError::Migration)?;

    create_test_user(connection)?;

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
        let conn = self.pool.get()?;

        Ok(conn)
    }
}

// https://stackoverflow.com/a/57717533
pub fn init_and_get_connection_pool() -> Result<ConnPool, DBError> {
    let db_location = database_location();
    init(&db_location)?;

    let pool = Pool::builder()
        .connection_customizer(Box::new(ConnOptions))
        .build(ConnectionManager::<SqliteConnection>::new(&db_location))?;

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
