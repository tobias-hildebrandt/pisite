"""Implements basic authentication"""
import passlib
import passlib.hash
import json
import unittest
import zxcvbn
import copy

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
    
    def create_user(self, username, plaintext_password, groups=None):
        """
        Add a user, given a password and list of groups.
        Hashes password using bcrypt.
        Only adds a user if everything is successful
        Raises UserExistsException if user already exists or parameters are invalid
        Raises GroupExistenceException if any group doesn't exist
        Raises WeakPasswordException if the password is too weak
        """
        # TODO: make groups variadic??
        # if no groups is empty, make sure we assign the user to the default group(s)
        if groups is None or len(groups) == 0:
            groups = BasicAuth.DEFAULT_GROUPS

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

        # make sure password is strong enough
        results = zxcvbn.zxcvbn(plaintext_password, user_inputs=[username])
        if results["score"] <= 2: # 2 and below is too weak
            raise WeakPasswordException(results)
        
        # hash the password
        hash_combo = passlib.hash.bcrypt.hash(plaintext_password).split('$')[-1]

        salt = hash_combo[:22] # first 22 characters
        hashed_password = hash_combo[22:] # everything after 22nd character

        # print("hash combo: {}\nsalt: {}\npass: {}\n".format(hash_combo,salt,hashed_password))

        # form details dict, 
        user = {'password': hashed_password, 'salt': salt, 'groups': set(groups)}
        
        # print ("adding user {}".format(user))

        # convert groups to list to json-ize it to a json array
        user_for_json = copy.deepcopy(user)
        user_for_json["groups"] = list(user_for_json["groups"])

        # try to json-ize it, raise any exceptions on failure to jsonize 
        json.dumps({username: user_for_json})

        # add the user 
        self._users[username] = user

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
        # make sure to turn groups into list so that it can become json array
        users_for_json = copy.deepcopy(self._users)
        for user in users_for_json:
            users_for_json[user]["groups"] = list(users_for_json[user]["groups"])

        groups_for_json = list(copy.deepcopy(self._groups))

        with open(filename, 'w') as write_file: # overwrite the file
            write_file.write(json.dumps({"groups": groups_for_json, "users": users_for_json}, indent=2))

    def load_from_file(self, filename):
        """
        Clears all information and repopulates with user and group information from file
        """
        with open(filename, 'r') as read_file:
            json_data = json.loads(read_file.read())
        
        self._groups = set(json_data["groups"])
        users = json_data["users"]

        for user in users:
            groups_set = set(users[user]["groups"])
            users[user]["groups"] = groups_set

        self._users = users
        
    def _assert_group_existence(self, group, exists):
        """
        Asserts that a group is valid and exists
        Raises TypeError if any group is not a string
        Raises GroupExistenceException if group does not exist
        """
        if not isinstance(group, str):
            raise TypeError("group must be a string")
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