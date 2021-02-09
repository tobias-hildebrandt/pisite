"""Implements basic authentication"""
import passlib
import passlib.hash
import json
import unittest
import zxcvbn
import copy
import yaml
import secrets
import datetime

# TODO: add permissions to groups
# TODO: add changing password
# TODO: add user information page, displaying groups and group permissions

class BasicAuth:
    """Allows for basic authentication, including registration keys, password encryption, and group permissions"""

    # list of groups that users are added to if no groups are specified
    _DEFAULT_GROUPS = {"default"}
    # default registration key length in bytes
    _KEY_LENGTH = 64
    # default key expiration offset as timedelta
    _DEFAULT_KEY_EXPIRATION_OFFSET = datetime.timedelta(days=3)

    def __init__(self):
        """Constructor that does not read from file, thus is empty"""
        self._users = dict()
        self._groups = set()
        self._registration_keys = dict()

        # add default groups to _groups
        self._groups.update(BasicAuth._DEFAULT_GROUPS)
    
    def create_user(self, username, plaintext_password, reg_key_string=None, groups=None, force=False) -> str:
        """
        Add a user, given a password. Accepts list of groups or uses groups associated with registration key.
        Returns created user's username # TODO: return user dict?
        Can force creation without registration key or group list.
        If registration key is supplied, the account will use the groups associated with the registration key, not the groups parameter.
        Hashes password using bcrypt.
        Only adds a user if everything is successful
        Raises UserExistsException if user already exists or parameters are invalid
        Raises GroupExistenceException if any group doesn't exist
        Raises WeakPasswordException if the password is too weak
        Raises BadRegistrationKeyException if registration_key is invalid
        """
        # if not force, make sure reg_key_string is a string
        if force is False and not isinstance(reg_key_string, str):
            # if key string is not given
            if reg_key_string is None:
                raise BadRegistrationKeyException(reg_key_string)
            # else key string is given but not a string
            else:
                raise TypeError("reg_key_string must be a string, not {}".format(type(reg_key_string)))

        # if given a registration key string, make sure we use the groups associated with said key
        if reg_key_string is not None:
            # will raise BadRegistrationKeyException if key doesn't exist
            try:
                reg_key = self._registration_keys[reg_key_string]
            except KeyError:
                raise BadRegistrationKeyException(reg_key_string)
            # will throw keyerror if format of self._registration_keys is messed up
            groups = reg_key["groups"]

        # if no groups is empty, make sure we assign the user to the default group(s)
        if groups is None or len(groups) == 0:
            groups = BasicAuth._DEFAULT_GROUPS

        if not isinstance(groups, set):
            raise TypeError("groups must be a set")

        # make sure each group exists
        for group in groups:
            self._assert_group_existence(group, True)
        
        # make sure user does not exist
        self._assert_user_existence(username, False)
        
        # verify that plaintext_password is a string
        if not isinstance(plaintext_password, str):
            raise TypeError("plaintext_password should be a string")
        
        # only check these things if not forced to create account
        if not force:
            # make sure password is strong enough
            results = zxcvbn.zxcvbn(plaintext_password, user_inputs=[username])
            if results["score"] <= 2: # 2 and below is too weak
                raise WeakPasswordException(results)

            # make sure that the registration key is valid
            # if a registration key is not given AND force is false, this will raise an exception
            if not reg_key_string in self._registration_keys:
                raise BadRegistrationKeyException(reg_key_string)

        # hash the password
        hash_combo = passlib.hash.bcrypt.hash(plaintext_password).split('$')[-1]

        salt = hash_combo[:22] # first 22 characters
        hashed_password = hash_combo[22:] # everything after 22nd character

        # print("hash combo: {}\nsalt: {}\npass: {}\n".format(hash_combo,salt,hashed_password))

        # form user detail dict
        user = {"password": hashed_password, "salt": salt, "groups": set(groups), "registration_key": reg_key_string}
        
        # print ("adding user {}".format(user))

        # convert groups to list to json-ize it to a json array
        user_for_json = copy.deepcopy(user)
        user_for_json["groups"] = list(user_for_json["groups"])

        # try to json-ize it, raise any exceptions on failure to jsonize 
        json.dumps({username: user_for_json})

        # add the user 
        self._users[username] = user

        # invalidate the registration key if given
        if reg_key_string is not None:
            del self._registration_keys[reg_key_string]
        
        return username

    def validate_user(self, username, plaintext_password_input) -> bool:
        """
        Validates login details.
        Returns True if valid, False if invalid.
        Raises UserExistenceException if user does not exist
        """
        # make sure user exists
        self._assert_user_existence(username, True)

        hashed_password_real = self._users[username]["password"]
        salt = self._users[username]["salt"]

        # print("salt is {}".format(salt))
        # print("real passhash is:  {}".format(hashed_password_real))

        # passing salt in hash() is deprecated
        # hashed_combo_input = passlib.hash.bcrypt.hash(plaintext_password_input, salt=salt).split('$')[-1]
        hashed_combo_input = passlib.hash.bcrypt.using(salt=salt).hash(plaintext_password_input).split('$')[-1]
        
        hashed_password_input = hashed_combo_input[22:] # everything after 22nd character
        
        # print("input passhash is: {}\n".format(hashed_password_input))
        
        return hashed_password_input == hashed_password_real

    def create_groups(self, *groups):
        """
        Adds groups.
        Will not add any group if one group is invalid or already exists
        Raises GroupExistenceException if group does not exist
        Raises TypeError if any group is not a string
        """
        # make sure all requested groups don't exist
        for group in groups:
            self._assert_group_existence(group, False)
        
        # add the groups
        self._groups.update(groups)

    def create_keys(self, num, expiration=None, groups=None) -> list:
        """
        Returns a list of new permission keys associated with the select groups
        Raises GroupExistenceException if any group does not exist
        Raises TypeError if expiration is not timedate
        Will not make any keys if any group does not exist
        """

        # set default datetime
        if expiration == None:
            expiration = datetime.datetime.now() + BasicAuth._DEFAULT_KEY_EXPIRATION_OFFSET

        # give default groups if none specified
        # also, check if groups is iterable with len()
        try:
            if groups == None or len(groups) == 0:
                groups = BasicAuth._DEFAULT_GROUPS
        except TypeError:
            raise TypeError("groups must be iterable, {} is not".format(type(groups)))
        
        # make sure groups isn't a string (which is iterable but not what we want)
        if isinstance(groups, str):
            raise TypeError("groups must not be string")

        # make sure expiration is a datetime
        if not isinstance(expiration, datetime.datetime):
            raise TypeError("expiration must be timedate, not {}".format(type(expiration)))
        
        # already checked if group is iterable
        for group in groups:
            self._assert_group_existence(group, True)
    
        list_of_keys=list()
        for _ in range(num):
            keep_going = True
            # make sure there's no collision
            while keep_going:
                # generate random hex token
                key_string = secrets.token_hex(BasicAuth._KEY_LENGTH)

                # if no collision in stored keys and not-yet stored keys
                if key_string not in self._registration_keys and key_string not in list_of_keys:
                    keep_going = False # don't loop
                    list_of_keys.append(key_string) # add the key to our temp list
                # else we have hit the jackpot and made a collision
                else:
                    print("buy a lottery ticket")
                    # keep looping
        
        # make dict that associates the key with the groups and expiration
        key_dict=dict()
        for key in list_of_keys:
            key_dict.update({key: {"expiration": expiration, "groups": set(groups)}})
        
        # add it to the store with given groups
        self._registration_keys.update(key_dict)

        # return the keys
        return list_of_keys

    def add_user_to_groups(self, user, *groups):
        """
        Adds user to groups
        Will not add user to any groups if one group is invalid
        Raises UserExistenceException if user does not exist
        Raises GroupExistenceException if group does not exist
        Raises TypeError if any group is not a string
        """
        # make sure user exists
        self._assert_user_existence(user, True)
        
        # verify that all requested groups are strings and don't exist
        for group in groups:
            self._assert_group_existence(group, True)
        
        self._users[user]["groups"].add(*groups)
    
    def remove_user_from_group(self, user, group):
        """
        Removes user from group
        """
        self._assert_user_existence(user, True)
        self._assert_group_existence(group, True)

        user_groups = self.get_user_groups(user)

        user_groups.remove(group)

    def is_user_in_group(self, user, group) -> bool:
        """
        Returns whether or not a user is in a group
        Raises UserExistenceException if user does not exist
        Raises GroupExistenceException if group does not exist
        """
        # make sure user exists
        self._assert_user_existence(user, True)
        # make sure group exists
        self._assert_group_existence(group, True)

        #print("user {}\ngroup {}".format(user, group))

        return (group in self._users[user]["groups"])

    def get_user_groups(self, user) -> set:
        """
        Returns a copy of the set of group to which the user belongs
        Raises UserExistenceException if user does not exist
        """
        self._assert_user_existence(user, True)

        return self._users[user]["groups"]

    def get_users_in_group(self, group) -> set:
        """
        Return a set of copies of users which belong to the group
        """
        self._assert_group_existence(group, True)

        grouped_users = set()

        for user in self._users:
            if group in self._users[user]["groups"]:
                grouped_users.add(user)

        return grouped_users

    def delete_user(self, user):
        """
        Deletes a user
        Raises UserExistenceException if user does not exist
        """
        self._assert_user_existence(user, True)
        
        del self._users[user]
    
    def delete_group(self, group):
        """
        Deletes a group and removes all users from group
        Raises GroupExistenceException if group does not exist
        """
        self._assert_group_existence(group, True)

        for user in self.get_users_in_group(group):
            self.remove_user_from_group(user, group)
        
        self._groups.remove(group)

    def print_all(self):
        """
        Prints all users' usernames, hashed passwords, and groups
        """
        print(self._users)
        print(self._groups)
        
    def save_to_file(self, filename):
        """
        Saves all user and group information to a file
        """
        with open(filename, 'w') as write_file: # overwrite the file
            yaml.dump({"groups": self._groups, "users": self._users, "registration_keys": self._registration_keys}, write_file, indent=2)

    def load_from_file(self, filename):
        """
        Clears all information and repopulates with user and group information from file
        """
        with open(filename, 'r') as read_file:
            data = yaml.load(read_file, Loader=yaml.FullLoader)
        
        self._groups = data["groups"]
        self._users = data["users"]
        self._registration_keys = data["registration_keys"]
        
    def _assert_group_existence(self, group, exists):
        """
        Asserts that a group is valid and exists
        Raises TypeError if any group is not a string
        Raises GroupExistenceException if group does not exist
        """
        if not isinstance(group, str):
            raise TypeError("group must be a string, not a {}".format(type(group)))
        if (group in self._groups) != exists:
            raise GroupExistenceException(group, not exists)
    
    def _assert_user_existence(self, user, exists):
        """
        Asserts that a user is valid and exists
        Raises TypeError if any group is not a string
        Raises GroupExistenceException if group does not exist
        """
        if not isinstance(user, str):
            raise TypeError("user must be a string")
        if (user in self._users) != exists:
            raise UserExistenceException(user, not exists)

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class UserExistenceException(Error):
    """Exception raised if a user already exists or does not exist, depending on 'exists' attribute

    Attributes:
        username -- the username that already exists
        exists -- whether or not the user exists # TODO: remove? might be useless
    """

    def __init__(self, username, exists):
        self.username = username
        self.exists = exists

class GroupExistenceException(Error):
    """Exception raised if a group already exists or does not exist, depending on 'exists' attribute

    Attributes:
        group -- the group that already exists
        exists -- whether or not the group exists # TODO: remove? might be useless
    """

    def __init__(self, group, exists):
        self.group = group
        self.exists = exists

class WeakPasswordException(Error):
    """Exception raised if a password is too weak

    Attributes:
        results -- the results from zxcvbn
    """

    def __init__(self, results):
        self.results = results

class BadRegistrationKeyException(Error):
    """Exception raised if a registration key is not valid

    Attributes:
        key -- the invalid key
    """

    def __init__(self, key):
        self.key = key
