# pylint: disable=no-member
import passlib
import passlib.hash
import zxcvbn
import secrets
import os
import sqlalchemy
from sqlalchemy import create_engine, ForeignKey, select
from sqlalchemy import Column, Date, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, object_session
import datetime

from flask_sqlalchemy import SQLAlchemy

# https://stackoverflow.com/a/9695045
db = SQLAlchemy()

## create tables and models

class GroupUser(db.Model):
    # should be essentially invisible, simply acting as an association table
    __tablename__ = "group_user"

    # columns
    # composite primary key
    group_id = Column(Integer, ForeignKey("group.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)

class GroupRegKey(db.Model):
    # should be essentially invisible, simply acting as an association table
    __tablename__ = "group_regkey"

    # columns
    # composite primary key
    group_id = Column(Integer, ForeignKey("group.id"), primary_key=True)
    regkey_id = Column(Integer, ForeignKey("regkey.id"), primary_key=True)

class User(db.Model):
    __tablename__ = "user"
    
    # columns
    id = Column(Integer, primary_key=True) # auto-increments
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)

    # relations
    regkey = relationship("RegKey", 
        back_populates="user",
        uselist=False, # one to one
        cascade="all, delete, delete-orphan" # cascade on delete
    )

    groups = relationship(
        "Group",
        secondary=GroupUser.__table__,
        # primaryjoin="User.id==GroupUser.user_id",
        # secondaryjoin="GroupUser.group_id==Group.id",
        back_populates="users",
        uselist=True
    )

    def __init__(self, username, password, salt, regkey):
        self.username = username
        self.password = password
        self.salt = salt
        self.regkey = regkey
        if regkey is not None:
            self.groups = regkey.groups
            regkey.user = self

    def __repr__(self):
        return "id: {}, username: \'{}\', pass:salt: \'{}:{}\', regkey: {}, groups:{}".format(
            self.id,
            self.username, 
            self.password, 
            self.salt, 
            self.regkey,
            self.groups
        )

    def to_detail_dict(self):
        details = dict()
        details["username"] = self.username
        details["groups"] = list()
        for group in self.groups:
            details["groups"].append(group.name)
        
        return details

class Group(db.Model):
    __tablename__ = "group"

    # columns
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # relations

    users = relationship(
        "User",
        secondary=GroupUser.__table__,
        # primaryjoin="Group.id==GroupUser.group_id",
        # secondaryjoin="GroupUser.user_id==User.id",
        back_populates="groups",
        uselist=True
    )

    regkeys = relationship(
        "RegKey",
        secondary=GroupRegKey.__table__,
        back_populates="groups",
        uselist=True
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name
    
    def to_detail_dict(self):
        details = dict()
        details["group"] = self.name
        details["users"] = list()
        for user in self.users:
            details["users"].append(user.username)
        
        return details

class RegKey(db.Model):
    __tablename__ = "regkey"

    # columns
    id = Column(Integer, primary_key=True) # auto-increments
    user_id = Column(Integer, ForeignKey("user.id"))
    text = Column(String, unique=True, nullable=False) # actual text for regkey
    note = Column(String, nullable=False) # note about how/to whom regkey was given
    expiry = Column(Date, nullable=True) # should be null only after user is set

    # relations
    user = relationship("User", back_populates="regkey")
    
    groups = relationship(
        "Group",
        secondary=GroupRegKey.__table__,
        back_populates="regkeys",
        uselist=True
    )

    def __init__(self, text, note, expiry, groups):
        self.text = text
        self.note = note
        self.expiry = expiry
        if groups is None:
            groups = []
        self.groups = groups
        self.user_id = None
        
    def __repr__(self):
        return "{}, \'{}\', exp:{}, g:{}, u:{}".format(self.text, self.note, self.expiry, self.groups, None if self.user is None else self.user.username)

    def to_detail_dict(self):
        details = dict()
        details["text"] = self.text
        details["note"] = self.note
        details["user"] = self.user
        details["expiry"] = self.expiry
        details["groups"] = list()
        for group in self.groups:
            details["groups"].append(group.name)
        
        return details
##

## define functions
def attempt_add_user(username, plain_password, reg_key_text) -> (bool, str):
    
    if username is None or username == "":
            return False, "must provide username"

    if reg_key_text is None or reg_key_text == "":
        return False, "must provide registration key"

    user_exists = User.query.filter(User.username == username).first() is not None
    reg_key_exists = RegKey.query.filter(RegKey.text == reg_key_text).first() is not None

    if user_exists:
        return False, "username taken {}".format(username)

    if not reg_key_exists:
        return False, "reg key {} doesn't exist".format(reg_key_text)
        
    if not _is_password_strong_enough(plain_password, [username, reg_key_text]):
        return False, "password not strong enough"
        
    return _add_user(username, plain_password, reg_key_text, force=False)

def validate_user(username, plain_password) -> (bool, str):
    user = User.query.filter(User.username == username).first() # only one should exist anyways
            
    if user is None:
        return False, "unknown username {}".format(username)

    # fetch salt and real hashed password
    salt = user.salt
    hashed_password_real = user.password

    hashed_password_input, _ = _hash_password(plain_password, salt)

    # compare the hashed passwords
    valid = hashed_password_input == hashed_password_real

    if valid:
        return True, user
    else:
        return False, "incorrect password"
    

def add_reg_key(text, note, expiry, groups):
    regkey = RegKey(text, note, expiry, groups)
    db.session.add(regkey)
    db.session.commit()

    return True

def remove_reg_key(reg_key):
    # if reg_key not in self.store.reg_keys:
    #     return False
    # self.store.reg_keys.remove(reg_key)
    # self._save()
    # return True
    return False, "unimplemented"

def remove_user(username):
    # if username not in self.store.users.keys():
    #     return False
    # self.store.users[username] = None
    # self._save()
    # return True
    return False, "unimplemented"

def get_user(user_id):
    return User.query.filter(User.id == user_id).first()

def get_users():
    return User.query.all()

def get_groups():
    return Group.query.all()

def get_reg_keys():
    return RegKey.query.all()

def change_password(user: User, new_password) -> (bool, str):
    
    if user is None:
        return False, "must provide user"
    if not _is_password_strong_enough(new_password, [user.username, user.regkey.text if user.regkey is not None else None]):
        return False, "password not strong enough" 

    # make new salt too
    hashed_password, salt = _hash_password(new_password, None)

    user.password = hashed_password
    user.salt = salt

    # user should already be added to session, just need to commit
    db.session.commit()

    return True, user.username
    # return False, "unimplemented"

def _hash_password(plain_password, salt=None) -> (str, str):
    # split on '$' and pick last element to ignore $2b$12
    hash_combo = passlib.hash.bcrypt.using(salt=salt).hash(plain_password).split('$')[-1]

    # salt is first 22 characters
    salt = hash_combo[:22]

    # hashed+salted password is next 22 characters
    hashed_password = hash_combo[22:]

    return hashed_password, salt

def _add_user(username, plain_password, reg_key_text, force=False) -> (bool, str):
        
    if not force and reg_key_text is None:
        return False, "requires reg_key_text"

    reg_key = RegKey.query.filter(RegKey.text == reg_key_text).first()

    if reg_key is None and not force:
        return False, "bad reg_key"

    hashed_password, salt = _hash_password(plain_password)
    user = User(username, hashed_password, salt, reg_key)

    db.session.add(user)
    db.session.commit()

    return True, username

def _is_password_strong_enough(plain_password, context: list) -> bool:
    results = zxcvbn.zxcvbn(plain_password, user_inputs=context)

    return results["score"] > 2 

def _print_all():
    users_list = User.query.all()
    groups_list = Group.query.all()
    regkey_list = RegKey.query.all()

    print()
    print("USERS:")
    for u in users_list:
        print(u)
    print("GROUPS:")
    for g in groups_list:
        print(g)
    print("REGKEYS:")
    for r in regkey_list:
        print(r)
    print()

##