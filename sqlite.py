from enum import Enum
import sqlite3
from typing import Dict

class DBType(Enum):
    DISK = 1
    MEMORY = 2

class Database:
    con = None
    cur = None

    def __init__(self, dbtype: DBType, filename="db.sqlite"):
        if dbtype == DBType.DISK:
            self.con = sqlite3.connect(filename)
        else:
            self.con = sqlite3.connect(":memory:")

        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE accounts(username, password, datecreated)")
        self.cur.execute("CREATE TABLE games(creator, id, name, description, datecreated)")
        self.cur.execute("CREATE TABLE nodes(name, amount, id, parent, datecreated)")

        self.cur.execute("CREATE TABLE hashes(key, value)")
        self.cur.execute("CREATE TABLE authkeys(key, value)")

    def user_exists(self, username) -> bool:
        res = self.cur.execute(f"SELECT username FROM accounts WHERE username='{username}'")
        return not (res.fetchone() is None)

    def create_user(self, username, password, datecreated) -> None:
        self.cur.execute(f"INSERT INTO accounts VALUES('{username}', '{password}', {datecreated})")
        self.con.commit()

    def valid_user_password(self, username, password) -> Dict:
        res = self.cur.execute(f"SELECT * FROM accounts WHERE username='{username}' AND password='{password}'")
        res = res.fetchone()
        return {"username": res[0], "password": res[1], "datecreated": res[2]}

    def hash_exists(self, key, val) -> bool:
        res = self.cur.execute(f"SELECT key FROM hashes WHERE key='{key}' AND value='{val}'")
        return not (res.fetchone() is None)

    def delete_hash(self, key):
        self.cur.execute(f"DELETE FROM hashes WHERE key='{key}'")
        self.con.commit()

    def create_authkey(self, key, val):
        self.cur.execute(f"INSERT INTO authkeys VALUES('{key}', '{val}')")
        self.con.commit()

    def authkey_exists(self, key) -> bool:
        res = self.cur.execute(f"SELECT * FROM authkeys WHERE key='{key}'")
        return not (res.fetchone() is None)

    def create_game(self, creator, id, name, description, datecreated):
        self.cur.execute(f"INSERT INTO games VALUES('{creator}', '{id}', '{name}', '{description}', '{datecreated}')")
        self.con.commit()

    def delete_game(self, creator, id):
        self.cur.execute(f"DELETE FROM games WHERE creator='{creator}' AND id='{id}'")
        self.con.commit()

    def user_games(self, creator) -> Dict:
        res = self.cur.execute(f"SELECT * FROM games WHERE creator='{creator}'")
        res = res.fetchall()
        return res

    def game_exists(self, id) -> bool:
        res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}'")
        return not (res.fetchone() is None)

    def game_info(self, id) -> Dict:
        res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}'")
        res = res.fetchone()
        return {"creator": res[0], "id": res[1], "name": res[2], "description": res[3], "datecreated": res[4]}
