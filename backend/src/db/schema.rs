// @generated automatically by Diesel CLI.

diesel::table! {
    groups (id) {
        id -> Integer,
        groupname -> Text,
    }
}

diesel::table! {
    login_sessions (id) {
        id -> Integer,
        user_id -> Integer,
        expiration -> Timestamp,
    }
}

diesel::table! {
    reg_keys (id) {
        id -> Integer,
        reg_key -> Text,
        note -> Text,
    }
}

diesel::table! {
    reg_keys_groups (id) {
        id -> Integer,
        reg_key_id -> Integer,
        group_id -> Integer,
    }
}

diesel::table! {
    users (id) {
        id -> Integer,
        username -> Text,
        password_crypt -> Text,
    }
}

diesel::table! {
    users_groups (id) {
        id -> Integer,
        user_id -> Integer,
        group_id -> Integer,
    }
}

diesel::joinable!(login_sessions -> users (user_id));
diesel::joinable!(reg_keys_groups -> groups (group_id));
diesel::joinable!(reg_keys_groups -> reg_keys (reg_key_id));
diesel::joinable!(users_groups -> groups (group_id));
diesel::joinable!(users_groups -> users (user_id));

diesel::allow_tables_to_appear_in_same_query!(
    groups,
    login_sessions,
    reg_keys,
    reg_keys_groups,
    users,
    users_groups,
);
