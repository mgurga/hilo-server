import time, random
from flask import Flask, request, redirect, abort
from flask_cors import CORS
from markupsafe import escape
from sqlite import DBType, Database

gamesite = "http://localhost:5173/hilo" # no trailing /

db = Database(DBType.DISK)
app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "Welcome to the HiLo server endpoint!!! :)"

@app.route("/list/users", methods=["GET"])
def listusers():
    items = db.all_users()
    out = f"Total of {len(items)} element(s)<br/>"
    for i in items:
        print(i)
        out += f"username: '{i['username']}' password: '*' datecreated: {i['datecreated']}<br/>"
    return out

@app.route("/list/games", methods=["GET"])
def listgames():
    items = db.all_games()
    out = "Total of " + str(len(items)) + " elements<br/>"
    for i in items:
        out += f"creator: '{i['creator']}' name: '{i['name']}' description: '{i['description']}' id: '{i['id']}' datecreated: {i['datecreated']}<br/>"
    return out

@app.route("/list/nodes", methods=["GET"])
def listnodes():
    items = db.all_nodes()
    out = "Total of " + str(len(items)) + " elements<br/>"
    for i in items:
        out += f"name: '{i['name']}' amount: '{i['amount']}' parent: '{i['parent']}' id: '{i['id']}' datecreated: {i['datecreated']}<br/>"
    return out

@app.route("/api/register", methods=["GET"])
def register():
    usernm, passwd = request.args.get("user"), request.args.get("pass")
    print(f"registering username: '{usernm}' password: '{passwd}'")

    if db.user_exists(usernm):
        return redirect(f"{gamesite}/login#exists")
    else:
        db.create_user(usernm, passwd, time.time())
        return redirect(f"{gamesite}/login#registered")

@app.route("/api/signin", methods=["GET"])
def signin():
    usernm, passwd = request.args.get("user"), request.args.get("pass")
    acc = db.valid_user_password(usernm, passwd)
    if acc == None:
        return redirect(f"{gamesite}/login#incorrect") # user does not exists
    elif acc["password"] == passwd:
        return redirect(f"{gamesite}/login#{createhash(usernm)}#{usernm}")
    else:
        return redirect(f"{gamesite}/login#incorrect") # incorrect password

@app.route("/api/authkey/<string:uhash>/<string:usernm>", methods=["GET"])
def createauthkey(uhash, usernm):
    uhash, usernm = escape(uhash), escape(usernm)
    if db.hash_exists(uhash, usernm):
        db.delete_hash(uhash)
        ak = createauth(usernm)
        return ak
    else:
        return "invalid hash"

@app.route("/api/games/create", methods=["GET"])
def creategame():
    authkey = request.headers["authkey"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    gid = creategameid()
    newgame = {
        "creator": creator,
        "id": gid,
        "name": "New Game",
        "description": f"Newly created game by {creator}",
        "datecreated": time.time()
    }
    db.create_game(creator, gid, "New Game", f"Newly created game by {creator}", time.time())
    return newgame

@app.route("/api/games/delete", methods=["POST"])
def deletegame():
    authkey = request.headers["authkey"]
    gid = request.headers["id"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    db.delete_game(creator, gid)
    return ""

@app.route("/api/<string:usernm>/games", methods=["GET"])
def usergames(usernm):
    return db.user_games(usernm)

@app.route("/api/game/<string:gid>/info", methods=["GET"])
def gameinfo(gid):
    if not db.game_exists(gid):
        abort(404)
    return db.game_info(gid)

@app.route("/api/game/<string:gid>/nodes", methods=["GET"])
def gamenodes(gid):
    return db.game_nodes(gid)

@app.route("/api/games/info", methods=["POST"])
def gamenamedesc():
    authkey = request.headers["authkey"]
    gid = request.headers["id"]
    name = request.headers["name"]
    desc = request.headers["desc"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    db.update_game(gid, name, desc)
    return ""

@app.route("/api/nodes/create", methods=["GET"])
def createnode():
    authkey = request.headers["authkey"]
    name = request.headers["name"]
    amt = request.headers["amount"]
    parent = request.headers["parent"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    gid = createnodeid()
    db.create_node(name, float(amt), gid, parent, time.time())
    return gid

@app.route("/api/nodes/delete", methods=["POST"])
def deletenode():
    nid = request.headers["id"]
    parent = request.headers["parent"]

    creator = validauth(request.headers["authkey"])
    if creator == "":
        return abort(401)

    if db.game_exists(parent, creator):
        db.delete_node(nid)
    return ""

@app.route("/api/nodes/edit", methods=["POST"])
def editnode():
    nid = request.headers["id"]
    parent = request.headers["parent"]
    name = request.headers["name"]
    amt = request.headers["amount"]

    creator = validauth(request.headers["authkey"])
    if creator == "":
        return abort(401)

    if db.game_exists(parent, creator):
        db.update_node(nid, name, float(amt))
    return ""

@app.route("/api/recent/<int:amt>", methods=["GET"])
def recents(amt: int):
    return db.recent_games(amt)

def validauth(ak) -> str:
    creator = db.authkey(ak)
    if creator == None:
        return ""
    return creator["value"]

def creategameid() -> str:
    out = createid()
    while db.game_exists(out):
        out = createid()
    return out

def createnodeid() -> str:
    out = createid()
    while db.node_exists(out):
        out = createid()
    return out

def createhash(usernm: str):
    out = createid()
    while db.hash_exists(out):
        out = createid()
    db.create_hash(out, usernm)
    return out

def createauth(usernm: str):
    out = createid()
    while db.authkey_exists(out):
        out = createid()
    db.create_authkey(out, usernm)
    return out

def createid():
    pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(pool, k=20))