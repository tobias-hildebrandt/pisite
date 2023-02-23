-- SQLite enable foreign keys
PRAGMA foreign_keys = ON;

-- primary data tables
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_crypt TEXT NOT NULL
);

CREATE TABLE groups (
    id INTEGER NOT NULL PRIMARY KEY,
    groupname TEXT NOT NULL
);

CREATE TABLE reg_keys (
    id INTEGER NOT NULL PRIMARY KEY,
    reg_key TEXT NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE login_sessions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expiration DATETIME NOT NULL, -- UTC
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- pivots
CREATE TABLE users_groups (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(group_id) REFERENCES groups(id)
);

CREATE TABLE reg_keys_groups (
    id INTEGER NOT NULL PRIMARY KEY,
    reg_key_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY(reg_key_id) REFERENCES reg_keys(id),
    FOREIGN KEY(group_id) REFERENCES groups(id)
);
