"""Implements basic authentication"""
import passlib
import passlib.hash
import json
import unittest
import zxcvbn

# bcrypt hash $x$y$x
# x = algorithm
# y = log_2(rounds) (default "12" for bcrypt, 4<=y<=31)
# z = 22 chars of salt + 21 chars of hash

#hash = passlib.hash.bcrypt.hash("test123")
#print(hash)

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

class BasicAuth:
    """An object that contains all implementation details"""

    # list of groups that users are added to if no groups are specified
    DEFAULT_GROUPS = {"default"}

    def __init__(self):
        """Constructor that does not read from file, thus is empty"""
        self._users = dict()
        self._groups = set()

        # add default groups to _groups
        self._groups.update(BasicAuth.DEFAULT_GROUPS)
    
    def add_user(self, username, plaintext_password, groups=None):
        """
        Add a user, given a password and list of groups.
        Hashes password using bcrypt.
        Only adds a user if everything is successful
        Raises UserExistsException if user already exists or parameters are invalid
        Raises GroupExistenceException if any group doesn't exist
        Raises WeakPasswordException if the password is too weak
        """

        # if no groups is empty, make sure we assign the user to the default group(s)
        if groups is None or len(groups) == 0:
            groups = BasicAuth.DEFAULT_GROUPS

        # verify that groups is a set
        if not isinstance(groups, set):
            raise TypeError("groups should be a set")

        # verify that each group is a string
        for group in groups:
            if not isinstance(group, str):
                raise TypeError("group should only contain strings")
        
        # verify that username is a string
        if not isinstance(username, str):
            raise TypeError("username should be a string")
        
        # verify that plaintext_password is a string
        if not isinstance(plaintext_password, str):
            raise TypeError("plaintext_password should be a string")

        # if username already exists, throw exception
        if username in self._users:
            raise UserExistenceException(username, True)

        # if a desired group doesn't exist, throw exception
        for group in groups:
            if group not in self._groups:
                raise GroupExistenceException(group, False)

        # make sure password is strong enough
        results = zxcvbn.zxcvbn(plaintext_password, user_inputs=[username])
        if results["score"] <= 2: # 2 and below is too weak
            raise WeakPasswordException(results)
        
        # hash the password
        hash_combo = passlib.hash.bcrypt.hash(plaintext_password).split('$')[-1]

        salt = hash_combo[:22] # first 22 characters
        hashed_password = hash_combo[22:] # everything after 22nd character

        # print("hash combo: {}\nsalt: {}\npass: {}\n".format(hash_combo,salt,hashed_password))

        # form details dict, convert groups to list to json-ize it to a json array
        user_details = {'password': hashed_password, 'salt':salt, 'groups': list(groups)}

        # try to json-ize it, raise any exceptions on failure to jsonize 
        json.dumps({username: user_details})

        # add the user 
        self._users[username] = user_details

    def validate_user(self, username, plaintext_password_input) -> bool:
        """
        Validates login details.
        Returns True if valid, False if invalid.
        Raises UserExistenceException if user does not exist
        """
        # if username does not exists, throw exception
        if username not in self._users:
            raise UserExistenceException(username, False)

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
        # verify that all requested groups are strings and don't exist
        for group in groups:
            if not isinstance(group, str):
                raise TypeError("groups should only be strings")
            if group in self._groups:
                raise GroupExistenceException(group, True)
        
        # add the groups
        self._groups.update(groups)

    def user_in_group(self, user, group):
        """
        Returns whether or not a user is in a group
        Raises UserExistenceException if user does not exist
        Raises GroupExistenceException if group does not exist
        """
        # make sure user is valid
        if user not in self._users:
            raise UserExistenceException(user, False)

        if not isinstance(group, str):
            raise TypeError("groups should only be strings")
        if group not in self._groups:
            raise GroupExistenceException(group, False)
        

        return group in self._users[user]["groups"]

    def add_user_to_groups(self, user, *groups):
        """
        Adds user to groups
        Will not add user to any groups if one group is invalid
        Raises UserExistenceException if user does not exist
        Raises GroupExistenceException if group does not exist
        Raises TypeError if any group is not a string
        """
        if user not in self._users:
            raise UserExistenceException(user, False)
        
        # verify that all requested groups are strings and don't exist
        for group in groups:
            if not isinstance(group, str):
                raise TypeError("groups should only be strings")
            if group not in self._groups:
                raise GroupExistenceException(group, False)
        
        self._users[user]["groups"].update(*groups)

    def print_users(self):
        """
        Prints all users' usernames, hashed passwords, and groups
        """
        print(self._users)

    def save_to_file(self, filename):
        """
        Saves all user and group information to a file
        """

        with open(filename, 'w') as write_file: # overwrite the file
            # make sure to turn groups into list so that it can become json array
            write_file.write(json.dumps({"groups": list(self._groups), "users": self._users}, indent=2))

    def load_from_file(self, filename):
        """
        Clears all information and repopulates with user and group information from file
        """
        with open(filename, 'r') as read_file:
            json_data = json.loads(read_file.read())
        
        self._groups = set(json_data["groups"])
        self._users = json_data["users"]

    # TODO: test and use this
    def assert_group_existence(self, group, exists):
        """
        Asserts that a group is valid and exists
        Raises TypeError if any group is not a string
        Raises GroupExistenceException if group does not exist
        """
        if not isinstance(group, str):
            raise TypeError("groups should only be strings")
        if group in self._groups == exists:
            raise GroupExistenceException(group, exists)

if __name__ == "__main__":
    
    import os
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner()

    print("\nstarting tests\n")
    runner.run(suite)
    print("\ndone with tests\n")

    # auth = BasicAuth()
    # username = "user123"
    # password = "HorseCatCowPassword8484848"
    # auth.add_user(username, password, None)
    # success = auth.validate_user(username, password)
    # print("successful auth? {}".format(success))
    # auth.print_users()