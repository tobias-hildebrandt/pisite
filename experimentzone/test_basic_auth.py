
from basic_auth import BasicAuth, UserExistenceException, GroupExistenceException, WeakPasswordException
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
    
    def test_good_passwords(self):
        self.auth.add_user("user1", _GOOD_PASSWORD)
        self.auth.add_user("user2", "thisIsASecurePassword123@#@#@!")
        self.auth.add_user("user3", "ljasdhfjkasfdhljkKJHJKHKJHJKHKJ12312213##@#@$%@%")

    def test_good_usernames(self):
        self.auth.add_user("user1", _GOOD_PASSWORD)
        self.auth.add_user("user2", _GOOD_PASSWORD)
        self.auth.add_user("user3", _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 3)

    def test_good_groups(self):
        self.auth.create_groups("admin", "fileaccess")
        self.auth.add_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        self.auth.add_user("user2", _GOOD_PASSWORD, {"default"})
        self.auth.add_user("user3", _GOOD_PASSWORD, BasicAuth.DEFAULT_GROUPS)
        self.auth.add_user("user4", _GOOD_PASSWORD, {"admin", "fileaccess"})
        self.auth.add_user("user5", _GOOD_PASSWORD, {"admin", })
        self.auth.add_user("user6", _GOOD_PASSWORD, None)
        self.auth.add_user("user7", _GOOD_PASSWORD)
    
    def test_user_in_group(self):
        self.auth.create_groups("admin", "fileaccess")
        self.auth.add_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})

        self.assertTrue(self.auth.user_in_group("user1", "admin"))
        self.assertTrue(self.auth.user_in_group("user1", "fileaccess"))

        for group in BasicAuth.DEFAULT_GROUPS:
            self.assertFalse(self.auth.user_in_group("user1", group))

        self.auth.add_user("user2", _GOOD_PASSWORD, None)
        for group in BasicAuth.DEFAULT_GROUPS:
            self.assertTrue(self.auth.user_in_group("user2", group))


    def test_good_group_creations(self):
        self.auth.create_groups("group1")
        self.auth.create_groups("group2")
        self.auth.create_groups("group3")
        self.assertEqual(len(self.auth._groups), 3+len(BasicAuth.DEFAULT_GROUPS)) 
    
    def test_good_validation(self):
        self.auth.add_user("user123", _GOOD_PASSWORD)
        self.assertTrue(self.auth.validate_user("user123", _GOOD_PASSWORD))

    def test_good_save_and_load(self):
        auth1 = BasicAuth()
        auth1.create_groups("admin", "fileaccess")
        auth1.add_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        auth1.add_user("user2", _GOOD_PASSWORD, {"default"})
        auth1.save_to_file(TestBasicAuth.temp_filename)

        auth2 = BasicAuth()
        auth2.load_from_file(TestBasicAuth.temp_filename)

        self.assertSetEqual(auth1._groups, auth2._groups)
        self.assertDictEqual(auth1._users, auth2._users)

    def test_repeated_username(self):
        self.auth.add_user("sameuser", _GOOD_PASSWORD)
        with self.assertRaises(UserExistenceException):
            self.auth.add_user("sameuser", _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 1)

    def test_nonstring_usernames(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.add_user(obj, _GOOD_PASSWORD)
        self.assertEqual(len(self.auth._users), 0)
        
    def test_nonstring_passwords(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.add_user("user", obj)
        self.assertEqual(len(self.auth._users), 0)
    
    def test_invalid_groups(self):
        with self.assertRaises(TypeError):
            self.auth.add_user("user1", _GOOD_PASSWORD, {"this": "should", "fail": "please"})
        with self.assertRaises(TypeError):
            self.auth.add_user("user2", _GOOD_PASSWORD, 123456)
        with self.assertRaises(TypeError):
            self.auth.add_user("user3", _GOOD_PASSWORD, "notagrouplist")
        with self.assertRaises(TypeError):
            self.auth.add_user("user4", _GOOD_PASSWORD, ["this is a string", 123123, {"this": "isn't a string"}])
        self.assertEqual(len(self.auth._users), 0)

    def test_repeated_group_creations(self):
        self.auth.create_groups("first", "second")
        before_groups = self.auth._groups
        with self.assertRaises(GroupExistenceException) as context:
            self.auth.create_groups("first")
        self.assertEqual(context.exception.exists, True)
        after_groups = self.auth._groups
        self.assertSetEqual(before_groups, after_groups)

    def test_invalid_group_creations(self):
        for obj in _NOT_STRINGS:
            with self.assertRaises(TypeError):
                self.auth.create_groups(obj)
        self.assertSetEqual(self.auth._groups, BasicAuth.DEFAULT_GROUPS) 

    def test_bad_passwords(self):
        bad_passwords = [
            "password",
            "123abc",
            "badpassword123"
        ]
        for i, password in enumerate(bad_passwords):
            with self.assertRaises(WeakPasswordException):
                self.auth.add_user("user{}".format(i), password)
    
    def test_bad_validation(self):
        self.auth.add_user("user1", _GOOD_PASSWORD)
        with self.assertRaises(UserExistenceException) as context:
            self.auth.validate_user("user2", "doesn't matter")
        self.assertEqual(context.exception.exists, False)

        self.assertFalse(self.auth.validate_user("user1", "not the right password"))
        self.assertFalse(self.auth.validate_user("user1", _GOOD_PASSWORD+" "))
    
    def test_load_file_different(self):
        auth1 = BasicAuth()
        auth1.create_groups("admin", "fileaccess")
        auth1.add_user("user1", _GOOD_PASSWORD, {"admin", "fileaccess"})
        auth1.add_user("user2", _GOOD_PASSWORD, {"default"})
        auth1.save_to_file(TestBasicAuth.temp_filename)

        auth2 = BasicAuth()
        auth2.load_from_file(TestBasicAuth.temp_filename)

        auth3 = BasicAuth()

        self.assertNotEqual(len(auth2._groups), len(auth3._groups))
        self.assertNotEqual(len(auth2._users), len(auth3._users))
 
if __name__ == "__main__":
    unittest.main()