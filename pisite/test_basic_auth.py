
from basic_auth import BasicAuth, UserExistenceException, GroupExistenceException, WeakPasswordException, Error # pylint ignore:import-error
import unittest
import tempfile

# TODO: test good and bad passwords from some list?

_NOT_STRINGS = [
    {"dict": "isn't", "a": "string"},
    ["list", "isn't", "a", "string"],
    12345
]

_GOOD_PASSWORD = "SecurePassword1!"

class TestBasicAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TestBasicAuth.temp_filename = tempfile.NamedTemporaryFile(delete=False).name
        print("temp file is {}".format(TestBasicAuth.temp_filename))

    @classmethod
    def tearDownClass(cls):
        import os
        os.remove(TestBasicAuth.temp_filename)
    
    # run before each test
    def setUp(self):
        self.auth = BasicAuth()

        # clear the temp file
        with open(TestBasicAuth.temp_filename, 'w') as temp_file:
            temp_file.write("") 

    # run after each test    
    def tearDown(self):
        del self.auth

    def test_big_test(self):
        self.auth.create_groups("group1", "group2", "group3")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"group1", "group2"})
        self.auth.create_user("user2", _GOOD_PASSWORD, {"group2"})
        self.auth.add_user_to_groups("user1", "group3")
        self.auth.remove_user_from_group("user1", "group3")
        self.auth.add_user_to_groups("user1", "group3")
        self.auth.delete_group("group3")
        self.assertTrue(self.auth.is_user_in_group("user1", "group2"))
        with self.assertRaises(GroupExistenceException) as context:
            self.auth.is_user_in_group("user1", "group3")
        self.assertFalse(context.exception.exists)
        self.auth.save_to_file(TestBasicAuth.temp_filename)
        self.auth._users = None
        self.auth._groups = None
        self.auth.load_from_file(TestBasicAuth.temp_filename)
        self.auth.create_user("user3", _GOOD_PASSWORD, {"group1"})
        self.assertEqual(len(self.auth.get_users_in_group("group1")), 2)
        self.assertEqual(len(self.auth._users), 3)
        self.assertEqual(len(self.auth._groups), 2 + len(BasicAuth._DEFAULT_GROUPS))
    
    def test_good_passwords(self):
        self.auth.create_user("user1", _GOOD_PASSWORD)
        self.auth.create_user("user2", "thisIsASecurePassword123@#@#@!")
        self.auth.create_user("user3", "ljasdhfjkasfdhljkKJHJKHKJHJKHKJ12312213##@#@$%@%")

    def test_good_usernames(self):
        self.auth.create_user("user1", _GOOD_PASSWORD)
        self.auth.create_user("user2", _GOOD_PASSWORD)
        self.auth.create_user("user3", _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 3)

    def test_good_groups(self):
        self.auth.create_groups("admin", "fileaccess")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        self.auth.create_user("user2", _GOOD_PASSWORD, {"default"})
        self.auth.create_user("user3", _GOOD_PASSWORD, BasicAuth._DEFAULT_GROUPS)
        self.auth.create_user("user4", _GOOD_PASSWORD, {"admin", "fileaccess"})
        self.auth.create_user("user5", _GOOD_PASSWORD, {"admin", })
        self.auth.create_user("user6", _GOOD_PASSWORD, None)
        self.auth.create_user("user7", _GOOD_PASSWORD)
    
    def test_user_in_group(self):
        self.auth.create_groups("admin", "fileaccess")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})

        self.assertTrue(self.auth.is_user_in_group("user1", "admin"))
        self.assertTrue(self.auth.is_user_in_group("user1", "fileaccess"))

        for group in BasicAuth._DEFAULT_GROUPS:
            self.assertFalse(self.auth.is_user_in_group("user1", group))

        self.auth.create_user("user2", _GOOD_PASSWORD, None)
        for group in BasicAuth._DEFAULT_GROUPS:
            self.assertTrue(self.auth.is_user_in_group("user2", group))

    def test_get_user_groups(self):
        self.auth.create_groups("group1", "group2")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"group1"})
        self.auth.add_user_to_groups("user1", "group2")
        groups = self.auth.get_user_groups("user1")

        expected_groups = {"group1", "group2"}

        self.assertSetEqual(groups, expected_groups)

    def test_good_group_creations(self):
        self.auth.create_groups("group1")
        self.auth.create_groups("group2")
        self.auth.create_groups("group3", "group4")
        self.assertEqual(len(self.auth._groups), 4+len(BasicAuth._DEFAULT_GROUPS)) 
    
    def test_good_validation(self):
        self.auth.create_user("user123", _GOOD_PASSWORD)
        self.assertTrue(self.auth.validate_user("user123", _GOOD_PASSWORD))

    def test_good_user_in_group(self):
        self.auth.create_user("test1", _GOOD_PASSWORD)
        for group in BasicAuth._DEFAULT_GROUPS:
            self.assertTrue(self.auth.is_user_in_group("test1", group))

    def test_good_add_user_to_group(self):
        self.auth.create_user("test1", _GOOD_PASSWORD)
        self.auth.create_groups("group1")
        self.auth.add_user_to_groups("test1", "group1")
        self.assertTrue(self.auth.is_user_in_group("test1", "group1"))

    def test_good_save_and_load(self):
        auth1 = BasicAuth()
        auth1.create_groups("admin", "fileaccess")
        auth1.create_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        #print("auth1 users after 1: {}".format(auth1._users))
        auth1.create_user("user2", _GOOD_PASSWORD, {"default"})
        #print("auth1 users after 2: {}".format(auth1._users))
        auth1.save_to_file(TestBasicAuth.temp_filename)
        #print("auth1 users after save: {}".format(auth1._users))

        auth2 = BasicAuth()
        auth2.load_from_file(TestBasicAuth.temp_filename)
        
        #print("auth2 users: {}".format(auth2._users))

        self.assertSetEqual(auth1._groups, auth2._groups)
        self.assertDictEqual(auth1._users, auth2._users)

    def test_good_delete_user(self):
        self.auth.create_user("user1", _GOOD_PASSWORD)
        self.auth.create_groups("group1")
        self.auth.add_user_to_groups("user1", "group1")

        self.auth.delete_user("user1")

        self.assertEqual(len(self.auth._users), 0)
        self.assertEqual(len(self.auth._groups), len(BasicAuth._DEFAULT_GROUPS) + 1)

    def test_good_delete_group(self):
        self.auth.create_groups("group1", "group2")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"group1", "group2"})
        self.auth.create_user("user2", _GOOD_PASSWORD, {"group1"})

        self.auth.delete_group("group1")

        user1_expected_groups = set()
        user1_expected_groups.add("group2")

        self.assertSetEqual(self.auth.get_user_groups("user1"), user1_expected_groups)
        self.assertSetEqual(self.auth.get_user_groups("user2"), set()) 

    def test_good_get_users_in_group(self):
        self.auth.create_groups("group1")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"group1"})
        self.auth.create_user("user2", _GOOD_PASSWORD, {"group1"})
        
        expected_users = {"user1", "user2"}
        
        self.assertSetEqual(expected_users, self.auth.get_users_in_group("group1"))

    def test_good_remove_user_from_group(self):
        self.auth.create_groups("group1", "group2")
        self.auth.create_user("user1", _GOOD_PASSWORD, {"group1", "group2"})

        self.auth.remove_user_from_group("user1", "group1")

        expected_groups = set()
        expected_groups.add("group2")

        self.assertSetEqual(self.auth.get_user_groups("user1"), expected_groups)

    def test_good_key_creation(self):
        key = self.auth.create_keys(1)[0]
        self.assertEqual(len(key), BasicAuth._KEY_LENGTH * 2)
        self.assertSetEqual(self.auth._registration_keys[key]["groups"], self.auth._DEFAULT_GROUPS)
        self.assertEqual(len(self.auth._registration_keys), 1)

    def test_good_keys_creation(self):
        num_of_keys = 10
        key_list = self.auth.create_keys(num_of_keys)

        self.assertEqual(len(key_list), num_of_keys)

        for key in key_list:
            self.assertEqual(key_list.count(key), 1)
            self.assertSetEqual(self.auth._registration_keys[key]["groups"], self.auth._DEFAULT_GROUPS)

        self.assertEqual(len(self.auth._registration_keys), 10)

    def test_good_key_creations_with_group(self):
        num_of_keys = 10
        groups = {"group1", "group2"}

        self.auth.create_groups(*groups)
        
        key_list = self.auth.create_keys(num_of_keys, groups=groups)

        self.assertEqual(len(key_list), num_of_keys)

        for key in key_list:
            self.assertEqual(key_list.count(key), 1)
            self.assertSetEqual(self.auth._registration_keys[key]["groups"], groups)

    def test_repeated_username(self):
        self.auth.create_user("sameuser", _GOOD_PASSWORD)
        with self.assertRaises(UserExistenceException):
            self.auth.create_user("sameuser", _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 1)

    def test_nonstring_usernames(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.create_user(obj, _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 0)
        
    def test_nonstring_passwords(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.create_user("user", obj)
        self.assertEqual(len(self.auth._users), 0)
    
    def test_invalid_groups(self):
        with self.assertRaises(TypeError):
            self.auth.create_user("user1", _GOOD_PASSWORD, {"this": "should", "fail": "please"})
        with self.assertRaises(TypeError):
            self.auth.create_user("user2", _GOOD_PASSWORD, 123456)
        with self.assertRaises(TypeError):
            self.auth.create_user("user3", _GOOD_PASSWORD, "notagrouplist")
        with self.assertRaises(TypeError):
            self.auth.create_user("user4", _GOOD_PASSWORD, ["this is a string", 123123, {"this": "isn't a string"}])
        self.assertEqual(len(self.auth._users), 0)

    def test_repeated_group_creations(self):
        self.auth.create_groups("first", "second")
        before_groups = self.auth._groups.copy()
        with self.assertRaises(GroupExistenceException) as context:
            self.auth.create_groups("first")
        self.assertEqual(context.exception.exists, True)
        after_groups = self.auth._groups.copy()
        self.assertSetEqual(before_groups, after_groups)

    def test_invalid_group_creations(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.create_groups(obj)
        self.assertSetEqual(self.auth._groups, BasicAuth._DEFAULT_GROUPS) 

    def test_bad_passwords(self):
        bad_passwords = [
            "password",
            "123abc",
            "badpassword123"
        ]
        for i, password in enumerate(bad_passwords):
            with self.assertRaises(WeakPasswordException):
                self.auth.create_user("user{}".format(i), password)
    
    def test_bad_validation(self):
        self.auth.create_user("user1", _GOOD_PASSWORD)
        with self.assertRaises(UserExistenceException) as context:
            self.auth.validate_user("user2", "doesn't matter")
        self.assertEqual(context.exception.exists, False)

        self.assertFalse(self.auth.validate_user("user1", "not the right password"))
        self.assertFalse(self.auth.validate_user("user1", _GOOD_PASSWORD+" "))
    
    def test_load_file_different(self):
        auth1 = BasicAuth()
        auth1.create_groups("admin", "fileaccess")
        auth1.create_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        auth1.create_user("user2", _GOOD_PASSWORD, {"default"})
        auth1.save_to_file(TestBasicAuth.temp_filename)

        auth2 = BasicAuth()
        auth2.load_from_file(TestBasicAuth.temp_filename)

        auth3 = BasicAuth()

        self.assertNotEqual(len(auth2._groups), len(auth3._groups))
        self.assertNotEqual(len(auth2._users), len(auth3._users))
    
    def test_add_user_to_nonexistent_group(self):
        self.auth.create_groups("group1")
        self.auth.create_user("user1", _GOOD_PASSWORD)
        with self.assertRaises(GroupExistenceException) as context:
            self.auth.add_user_to_groups("user1", "group2")
        self.assertEqual(context.exception.exists, False)
    
    def test_add_nonexistent_user_to_group(self):
        self.auth.create_groups("group1")
        with self.assertRaises(UserExistenceException) as context:
            self.auth.add_user_to_groups("user1", "group1")
        self.assertEqual(context.exception.exists, False)
    
    def test_delete_nonexistent_user(self):
        self.auth.create_user("user1", _GOOD_PASSWORD)

        with self.assertRaises(UserExistenceException) as context:
            self.auth.delete_user("user2")
        self.assertEqual(context.exception.exists, False)

        self.assertEqual(len(self.auth._users), 1)

    def test_delete_nonexistent_group(self):
        self.auth.create_groups("group1", "group2")

        with self.assertRaises(GroupExistenceException) as context:
            self.auth.delete_group("group3")
        self.assertEqual(context.exception.exists, False)

        expected_groups = set()
        for group in BasicAuth._DEFAULT_GROUPS:
            expected_groups.add(group)
        expected_groups.add("group1")
        expected_groups.add("group2")

        self.assertSetEqual(self.auth._groups, expected_groups)
    
    def test_bad_key_creation(self):
        fails = [
            12312313, 
            {123123, 123123}, 
            [123,456,789], 
            "i'm a string"
        ]
        for fail in fails:
            with self.assertRaises(TypeError):
                self.auth.create_keys(1, groups=fail)
            with self.assertRaises(TypeError):
                self.auth.create_keys(1, expiration=fail)
        with self.assertRaises(TypeError):
            self.auth.create_keys(1, expiration=1231231231)
        self.assertEqual(len(self.auth._registration_keys), 0)
    
    def test_make_keys_with_nonexistent_groups(self):
        groups = {"not", "created", "yet"}
        with self.assertRaises(GroupExistenceException) as context:
            self.auth.create_keys(1, groups=groups)
        self.assertEqual(context.exception.exists, False)

        self.assertEqual(len(self.auth._registration_keys), 0)

if __name__ == "__main__":
    unittest.main()