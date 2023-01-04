use diesel::dsl::sql;
use diesel::prelude::*;
use diesel::{Connection, ConnectionResult, SqliteConnection};
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use rand::Rng;

use super::schema;

const DB_NAME: &str = "relay.sqlite3";

const MIGRATIONS: EmbeddedMigrations = embed_migrations!("sql");

#[derive(thiserror::Error, Debug)]
pub enum DBError {
    #[error("DBError::ConnectionError({0:?})")]
    ConnectionError(ConnectionError),
    #[error("DBError::MigrationError({0:?})")]
    MigrationError(Box<dyn std::error::Error + Send + Sync>),
    #[error("DBError::QueryError({0:?})")]
    QueryError(diesel::result::Error),
}

impl From<ConnectionError> for DBError {
    fn from(e: ConnectionError) -> Self {
        DBError::ConnectionError(e)
    }
}

impl From<diesel::result::Error> for DBError {
    fn from(e: diesel::result::Error) -> Self {
        DBError::QueryError(e)
    }
}

pub fn connect() -> ConnectionResult<SqliteConnection> {
    SqliteConnection::establish(DB_NAME)
}

#[derive(Queryable, Debug)]
pub struct ExistingUser {
    id: i32,
    username: String,
}

#[derive(Insertable, Debug)]
#[diesel(table_name = schema::users)]
pub struct NewUser {
    username: String,
}

pub fn create_dummy_user(connection: &mut SqliteConnection, username: &str) -> Result<(), DBError> {
    let new_user = NewUser {
        username: username.to_string(),
    };
    diesel::insert_into(schema::users::table)
        .values(&new_user)
        .execute(connection)?;
    let resulting_user: ExistingUser = schema::users::dsl::users
        .find(sql("last_insert_rowid()"))
        .get_result(connection)?;

    println!("created user: {:?}", resulting_user);

    Ok(())
}

pub fn print_all() -> Result<(), DBError> {
    let connection = &mut connect()?;

    // run migrations if needed
    let _migrations_run: Vec<_> = connection
        .run_pending_migrations(MIGRATIONS)
        .map_err(|e| DBError::MigrationError(e))?;

    // create some dummy users
    for _ in 0..10 {
        let num = rand::thread_rng().gen_range(0u16..100);
        let username = format!("testuser{}", num);
        if let Err(e) = create_dummy_user(connection, &username) {
            println!("error adding user with username '{username}': {e}");
        }
    }

    // load all users
    let users = schema::users::dsl::users.load::<ExistingUser>(connection)?;

    // print how many
    println!("got all {} users from DB", users.len());

    Ok(())
}
