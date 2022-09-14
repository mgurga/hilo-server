import unittest
from sqlite import DBType, Database

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database(DBType.MEMORY)

    def test_user_create_read_exist(self):
        self.db.create_user("hello", "world", 12345.6789)
        res = self.db.valid_user_password("hello", "world")
        self.assertEqual(res["username"], "hello")
        self.assertEqual(res["password"], "world")
        self.assertEqual(res["datecreated"], 12345.6789)
        self.assertTrue(self.db.user_exists("hello"))

    def test_user_does_not_exists(self):
        self.assertFalse(self.db.user_exists("randomuser"))
        self.assertIsNone(self.db.valid_user_password("user", "pass"))

    def test_hash_create_exist(self):
        self.db.create_hash("foo", "bar")
        self.assertTrue(self.db.hash_exists("foo", "bar"))
    
    def test_hash_delete(self):
        self.db.create_hash("foo", "bar")
        self.assertTrue(self.db.hash_exists("foo", "bar"))
        self.db.delete_hash("foo")
        self.assertFalse(self.db.hash_exists("foo", "bar"))

    def test_game_create_exists_delete(self):
        self.db.create_game("foo", "1D151MP0R74N7", "game", "test game", 123456.7890)
        self.assertTrue(self.db.game_exists("1D151MP0R74N7"))
        self.db.delete_game("foo", "1D151MP0R74N7")
        self.assertFalse(self.db.game_exists("1D151MP0R74N7"))
    
    def test_game_info(self):
        self.db.create_game("foo", "1D151MP0R74N7!", "game", "test game", 123456.7890)
        res = self.db.game_info("1D151MP0R74N7!")
        self.assertEqual(res, {"creator": "foo", "id": "1D151MP0R74N7!", "name": "game", "description": "test game", "datecreated": 123456.7890})

    def test_game_uppdate(self):
        self.db.create_game("foo", "1D151MP0R74N7!!", "game", "test game", 123456.7890)
        res = self.db.game_info("1D151MP0R74N7!!")
        self.assertEqual(res["name"], "game")
        self.assertEqual(res["description"], "test game")
        self.db.update_game("1D151MP0R74N7!!", "better game", "new description")
        res = self.db.game_info("1D151MP0R74N7!!")
        self.assertEqual(res["name"], "better game")
        self.assertEqual(res["description"], "new description")

    def test_authkey_create_delete_exists(self):
        self.db.create_authkey("hello", "authkey")
        self.assertTrue(self.db.authkey_exists("hello"))
        self.db.delete_authkey("hello")
        self.assertFalse(self.db.authkey_exists("hello"))

    def test_authkey_undeclared(self):
        self.assertFalse(self.db.authkey_exists("notdeclared"))
        self.db.delete_authkey("notdeclared")

    def test_node_create_delete_exists(self):
        self.db.create_node("testnode", 123, "N0D31D", "P4R3N7", 12345.678)
        self.assertTrue(self.db.node_exists("N0D31D"))
        self.db.delete_node("N0D31D")
        self.assertFalse(self.db.node_exists("N0D31D"))

    def test_game_nodes(self):
        self.db.create_game("joe", "123", "node test", "i love nodes!!!", 9875.4321)
        self.db.create_node("node1", 5, "N0D31D1", "123", 9875.4333)
        self.db.create_node("node2", 10, "N0D31D2", "123", 9875.4444)
        self.db.create_node("node3", 15, "N0D31D3", "123", 9875.5555)
        res = self.db.game_nodes("123")
        self.assertEqual(res[0]["name"], "node1")
        self.assertEqual(res[1]["name"], "node2")
        self.assertEqual(res[2]["name"], "node3")
        res = self.db.game_nodes("123", "DESC")
        self.assertEqual(res[0]["name"], "node3")
        self.assertEqual(res[1]["name"], "node2")
        self.assertEqual(res[2]["name"], "node1")

if __name__ == '__main__':
    unittest.main()