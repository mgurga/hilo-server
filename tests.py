import unittest
from sqlite import DBType, Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(DBType.MEMORY)

    def test_user_create_read(self):
        self.db.create_user("hello", "world", 12345.6789)
        res = self.db.valid_user_password("hello", "world")
        self.assertEqual(res["username"], "hello")
        self.assertEqual(res["password"], "world")
        self.assertEqual(res["datecreated"], 12345.6789)

    def test_user_exists(self):
        self.assertTrue(self.db.user_exists("hello"))

    def test_user_does_not_exists(self):
        self.assertFalse(self.db.user_exists("randomuser"))

if __name__ == '__main__':
    unittest.main()