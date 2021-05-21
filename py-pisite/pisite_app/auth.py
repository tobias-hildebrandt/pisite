
import passlib
import passlib.hash
import json
import zxcvbn
import secrets
import os
import threading
import serde
import copy
import yaml

class User(serde.Model):
    username: serde.fields.Str()
    hashed_password: serde.fields.Str()
    salt: serde.fields.Str()
    reg_key: serde.fields.Str()

class Store(serde.Model):
    users: serde.fields.Dict(key=serde.fields.Str, value=serde.fields.Nested(User))
    reg_keys: serde.fields.Set(element=serde.fields.Str())

class Auth(object):

    def __init__(self, filepath):
        self.store = Store(dict(), set())
        self.filepath = filepath
        self.lock = threading.Lock()

        self._load()

    def attempt_add_user(self, username, plain_password, reg_key) -> (bool, str):
        if username in self.store.users.keys():
            return False, "username taken {}".format(username)
        if reg_key not in self.store.reg_keys:
            return False, "reg key {} doesn't exist".format(reg_key)
        if not self._password_strong_enough(plain_password, [username]):
            return False, "password not strong enough"
        
        if username is None or username == "":
            return False, "must provide username"
        
        if reg_key is None or reg_key == "":
            return False, "must provide registration key"
        
        return self._add_user(username, plain_password, reg_key, force=False)

    def validate_user(self, username, plain_password) -> (bool, str):
        if username not in self.store.users.keys():
            return False, "unknown username {}".format(username)
        
        # fetch salt and real hashed password
        salt = self.store.users[username].salt
        hashed_password_real = self.store.users[username].hashed_password

        hashed_password_input, _ = self._hash_password(plain_password, salt)

        # compare the hashed passwords
        valid = hashed_password_input == hashed_password_real

        if valid:
            return True, username
        else:
            return False, "incorrect password for user {}".format(username)

    def add_reg_key(self, reg_key):
        if reg_key in self.store.reg_keys:
            return False
        self.store.reg_keys.add(reg_key)
        self._save()
        return True

    def remove_reg_key(self, reg_key):
        if reg_key not in self.store.reg_keys:
            return False
        self.store.reg_keys.remove(reg_key)
        self._save()
        return True
    
    def remove_user(self, username):
        if username not in self.store.users.keys():
            return False
        self.store.users[username] = None
        self._save()
        return True

    def get_reg_keys(self):
        return self.store.reg_keys

    def get_usernames(self):
        return self.store.users.keys()

    def change_password(self, username, new_password) -> (bool, str):
        if username not in self.store.users.keys():
            return False, "unknown username {}".format(username)
        if not self._password_strong_enough(new_password, [username]):
            return False, "password not strong enough" 

        hashed_password, salt = self._hash_password(new_password, None)

        self.lock.acquire()

        self.store.users[username].hashed_password = hashed_password
        self.store.users[username].salt = salt

        self.lock.release()

        self._save()

        return True, username

    def _save(self):
        self.lock.acquire()
        # store_dict = self.store.to_dict()
        store_writable = yaml.dump(self.store)
        with open(self.filepath, 'w') as write_file:
            write_file.write(store_writable)
        self.lock.release()

    def _load(self):
        self.lock.acquire()
        with open(self.filepath, 'r') as read_file:
            # store_read = read_file.read()
            # try:
            new_store = yaml.load(read_file, Loader=yaml.Loader)
            if isinstance(new_store, Store):
                self.store = new_store
                print("STORE LOADED")
            else:
                print("ERROR: STORE NOT LOADED, NEW STORE CREATED")
                self.store = Store(dict(), set())
            # except yaml.error.YAMLError:
            #     print("ERROR: YAML ERROR, NEW STORE CREATED")
            #     self.store = Store(dict(), set())
        self.lock.release()

    def _hash_password(self, plain_password, salt=None) -> (str, str):
        # split on '$' and pick last element to ignore $2b$12
        hash_combo = passlib.hash.bcrypt.using(salt=salt).hash(plain_password).split('$')[-1]

        # salt is first 22 characters
        salt = hash_combo[:22]

        # hashed+salted password is next 22 characters
        hashed_password = hash_combo[22:]

        return hashed_password, salt

    def _add_user(self, username, plain_password, reg_key, force=False) -> (bool, str):
        if force is False:
            self.store.reg_keys.remove(reg_key)
        hashed_password, salt = self._hash_password(plain_password)
        user = User(username, hashed_password, salt, reg_key)
        self.lock.acquire()
        self.store.users[user.username] = user
        self.lock.release()
        self._save()
        return True, username

    def _password_strong_enough(self, plain_password, context: list) -> bool:
        results = zxcvbn.zxcvbn(plain_password, user_inputs=context)

        return results["score"] > 2 # return True if score > 2, else return False 

    def _print_all(self):
        print(yaml.dump(self.store))