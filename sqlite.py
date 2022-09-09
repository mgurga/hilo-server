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
            print(f"using sqlite backend in disk mode")
            self.con = sqlite3.connect(filename)
        else:
            print(f"using sqlite backend in memory mode")
            self.con = sqlite3.connect(":memory:")
        self.cur = self.con.cursor()

        print(f"sqlite3 version: {sqlite3.version}")
        print(f"sqlite_version version: {sqlite3.sqlite_version}")

        res = self.cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        res = res.fetchall()
        if len(res) != 5:
            self.cur.execute("CREATE TABLE accounts(username, password, datecreated)")
            self.cur.execute("CREATE TABLE games(creator, id, name, description, datecreated)")
            self.cur.execute("CREATE TABLE nodes(name, amount, id, parent, datecreated)")

            self.cur.execute("CREATE TABLE hashes(key, value)")
            self.cur.execute("CREATE TABLE authkeys(key, value)")

    # Misc/Raw operations (DO NOT USE)
    def all_users(self, order_by="ascending"):
        order_by = "ASC" if order_by == "ascending" else "DESC"
        res = self.cur.execute(f"SELECT * FROM accounts ORDER BY datecreated {order_by}")
        res = res.fetchall()
        out = []
        for acc in res:
            out.append({"username": acc[0], "password": acc[1], "datecreated": float(acc[2])})
        return out

    def all_games(self, order_by="ascending"):
        order_by = "ASC" if order_by == "ascending" else "DESC"
        res = self.cur.execute(f"SELECT * FROM games ORDER BY datecreated {order_by}")
        res = res.fetchall()
        out = []
        for game in res:
            out.append({"creator": game[0], "id": game[1], "name": game[2], "description": game[3], "datecreated": float(game[4])})
        return out

    def all_nodes(self, order_by="ascending"):
        order_by = "ASC" if order_by == "ascending" else "DESC"
        res = self.cur.execute(f"SELECT * FROM nodes ORDER BY datecreated {order_by}")
        res = res.fetchall()
        out = []
        for game in res:
            out.append({"name": game[0], "amount": float(game[1]), "id": game[2], "parent": game[3], "datecreated": float(game[4])})
        return out

    # User operations
    def user_exists(self, username: str) -> bool:
        res = self.cur.execute(f"SELECT username FROM accounts WHERE username='{username}'")
        return not (res.fetchone() is None)

    def create_user(self, username: str, password: str, datecreated: float) -> None:
        self.cur.execute(f"INSERT INTO accounts VALUES('{username}', '{password}', {datecreated})")
        self.con.commit()

    def valid_user_password(self, username: str, password: str) -> Dict:
        res = self.cur.execute(f"SELECT * FROM accounts WHERE username='{username}' AND password='{password}'")
        res = res.fetchone()
        if res is None:
            return None
        return {"username": res[0], "password": res[1], "datecreated": res[2]}

    # Hash operations
    def hash_exists(self, key: str, val="") -> bool:
        if val == "":
            res = self.cur.execute(f"SELECT * FROM hashes WHERE key='{key}'")
        else:
            res = self.cur.execute(f"SELECT * FROM hashes WHERE key='{key}' AND value='{val}'")
        return not (res.fetchone() is None)

    def create_hash(self, key: str, val: str):
        self.cur.execute(f"INSERT INTO hashes VALUES('{key}', '{val}')")
        self.con.commit()

    def delete_hash(self, key: str):
        self.cur.execute(f"DELETE FROM hashes WHERE key='{key}'")
        self.con.commit()

    # Authkey operations
    def create_authkey(self, key: str, val: str):
        self.cur.execute(f"INSERT INTO authkeys VALUES('{key}', '{val}')")
        self.con.commit()

    def authkey_exists(self, key: str) -> bool:
        res = self.cur.execute(f"SELECT * FROM authkeys WHERE key='{key}'")
        return not (res.fetchone() is None)

    def delete_authkey(self, key: str):
        self.cur.execute(f"DELETE FROM authkeys WHERE key='{key}'")
        self.con.commit()

    def authkey(self, key: str):
        res = self.cur.execute(f"SELECT * FROM authkeys WHERE key='{key}'")
        res = res.fetchone()
        if res is None:
            return None
        return {"key": res[0], "value": res[1]}

    # Game operations
    def create_game(self, creator: str, id: int, name: str, description: str, datecreated: float):
        self.cur.execute(f"INSERT INTO games VALUES('{creator}', '{id}', '{name}', '{description}', {datecreated})")
        self.con.commit()

    def delete_game(self, creator: str, id: str):
        self.cur.execute(f"DELETE FROM games WHERE creator='{creator}' AND id='{id}'")
        self.con.commit()

    def user_games(self, creator: str) -> Dict:
        res = self.cur.execute(f"SELECT * FROM games WHERE creator='{creator}'")
        res = res.fetchall()
        out = []
        for game in res:
            out.append({"creator": game[0], "id": game[1], "name": game[2], "description": game[3], "datecreated": float(game[4])})
        return out

    def game_exists(self, id: str, creator="") -> bool:
        if creator == "":
            res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}'")
        else:
            res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}' AND creator='{creator}'")
        return not (res.fetchone() is None)

    def game_info(self, id: str) -> Dict:
        res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}'")
        res = res.fetchone()
        if res is None:
            return None
        return {"creator": res[0], "id": res[1], "name": res[2], "description": res[3], "datecreated": float(res[4])}
    
    def update_game(self, id: str, name: str, desc: str):
        res = self.cur.execute(f"SELECT * FROM games WHERE id='{id}'")
        res = res.fetchone()
        if res is None:
            return None
        self.cur.execute(f"DELETE FROM games WHERE id='{res[1]}'")
        self.cur.execute(f"INSERT INTO games VALUES('{res[0]}', '{res[1]}', '{name}', '{desc}', {res[4]})")
        self.con.commit()

    def recent_games(self, amount: int):
        res = self.cur.execute(f"SELECT * FROM games ORDER BY datecreated ASC")
        res = res.fetchmany(amount)
        if res is None:
            return None
        out = []
        for game in res:
            out.append({"creator": game[0], "id": game[1], "name": game[2], "description": game[3], "datecreated": float(game[4])})
        return out

    # Node operations
    def create_node(self, name: str, amount: float, nid: str, parent: str, datecreated: float):
        self.cur.execute(f"INSERT INTO nodes VALUES('{name}', {amount}, '{nid}', '{parent}', {datecreated})")
        self.con.commit()

    def delete_node(self, nid: str):
        self.cur.execute(f"DELETE FROM nodes WHERE id='{nid}'")
        self.con.commit()

    def node_exists(self, nid: str):
        res = self.cur.execute(f"SELECT * FROM nodes WHERE id='{nid}'")
        return not (res.fetchone() is None)

    def update_node(self, nid: str, name: str, amount: float):
        res = self.cur.execute(f"SELECT * FROM nodes WHERE id='{nid}'")
        res = res.fetchone()
        if res is None:
            return None
        self.cur.execute(f"DELETE FROM nodes WHERE id='{res[2]}'")
        self.cur.execute(f"INSERT INTO nodes VALUES('{name}', {amount}, '{res[2]}', '{res[3]}', {res[4]})")
        self.con.commit()

    def game_nodes(self, game_id: str, order_by="ascending"):
        order_by = "ASC" if order_by == "ascending" else "DESC"
        res = self.cur.execute(f"SELECT * FROM nodes WHERE parent='{game_id}' ORDER BY datecreated {order_by}")
        res = res.fetchall()
        out = []
        for game in res:
            out.append({"name": game[0], "amount": float(game[1]), "id": game[2], "parent": game[3], "datecreated": float(game[4])})
        return out