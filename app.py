import time, random, json
from tinydb import TinyDB, Query, where
from flask import Flask, request, redirect, abort
from flask_cors import CORS
from markupsafe import escape

gamesite = "http://localhost:3000"
app = Flask(__name__)
CORS(app)

db = TinyDB("db.json")
accdb = db.table("accounts")
gamedb = db.table("games")
nodedb = db.table("nodes")

hashkv = db.table("hashes")
authkv = db.table("authkey")

@app.route("/")
def index():
    return "Welcome to the HiLo server endpoint!!! :)"

@app.route("/list/users", methods=["GET"])
def listusers():
    items = accdb.all()
    out = f"Total of {len(items)} element(s)<br/>"
    for i in items:
        print(i)
        out += f"username: '{i.get('username')}' password: '*' datecreated: {i.get('datecreated')}<br/>"
    return out

@app.route("/list/games", methods=["GET"])
def listgames():
    items = gamedb.all()
    out = "Total of " + str(len(items)) + " elements<br/>"
    for i in items:
        out += f"creator: '{i.get('creator')}' name: '{i.get('name')}' description: '{i.get('description')}' id: '{i.get('id')}' datecreated: {i.get('datecreated')}<br/>"
    return out

@app.route("/list/nodes", methods=["GET"])
def listnodes():
    items = nodedb.all()
    out = "Total of " + str(len(items)) + " elements<br/>"
    for i in items:
        out += f"name: '{i.get('name')}' amount: '{i.get('amount')}' parent: '{i.get('parent')}' id: '{i.get('id')}' datecreated: {i.get('datecreated')}<br/>"
    return out

@app.route("/api/register", methods=["GET"])
def register():
    usernm, passwd = request.args.get("user"), request.args.get("pass")
    print(f"registering username: '{usernm}' password: '{passwd}'")

    if accdb.contains(Query().username == usernm):
        return redirect(f"{gamesite}/login#exists")
    else:
        accdb.insert({"username": usernm, "password": passwd, "datecreated": time.time()})
        return redirect(f"{gamesite}/login#registered")

@app.route("/api/signin", methods=["GET"])
def signin():
    usernm, passwd = request.args.get("user"), request.args.get("pass")
    acc = accdb.get(Query().username == usernm)
    if acc == None:
        return redirect(f"{gamesite}/login#incorrect") # user does not exists
    elif acc.get("password") == passwd:
        return redirect(f"{gamesite}/login#{createhash(usernm)}#{usernm}")
    else:
        return redirect(f"{gamesite}/login#incorrect") # incorrect password

@app.route("/api/authkey/<string:uhash>/<string:usernm>", methods=["GET"])
def createauthkey(uhash, usernm):
    uhash, usernm = escape(uhash), escape(usernm)
    if hashkv.contains(Query().key == uhash and Query().value == usernm):
        hashkv.remove(Query().key == uhash)
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

    newgame = {
        "creator": creator,
        "id": creategameid(),
        "name": "New Game",
        "description": f"Newly created game by {creator}",
        "datecreated": time.time()
    }
    gamedb.insert(newgame)
    return newgame

@app.route("/api/games/delete", methods=["POST"])
def deletegame():
    authkey = request.headers["authkey"]
    gid = request.headers["id"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    gamedb.remove(Query().id == gid and Query().creator == creator)
    return ""

@app.route("/api/<string:usernm>/games", methods=["GET"])
def usergames(usernm):
    games = gamedb.search(where("creator") == usernm)
    out = []
    for g in games:
        out.append({
            "creator": g.get("creator"),
            "id": g.get("id"),
            "name": g.get("name"),
            "description": g.get("description"),
            "datecreated": g.get("datecreated")
        })
    return json.dumps(out)

@app.route("/api/game/<string:gid>/info", methods=["GET"])
def gameinfo(gid):
    g = gamedb.get(where("id") == gid)
    if g == None:
        abort(404)
    return {
        "creator": g.get("creator"),
        "id": g.get("id"),
        "name": g.get("name"),
        "description": g.get("description"),
        "datecreated": g.get("datecreated")
    }

@app.route("/api/game/<string:gid>/nodes", methods=["GET"])
def gamenodes(gid):
    nodes = nodedb.search(where("parent") == gid)
    out = []
    for n in nodes:
        out.append({
            "id": n.get("id"),
            "parent": n.get("parent"),
            "name": n.get("name"),
            "amount": n.get("amount"),
            "datecreated": n.get("datecreated")
        })
    return json.dumps(out)

@app.route("/api/games/info", methods=["POST"])
def gamenamedesc():
    authkey = request.headers["authkey"]
    gid = request.headers["id"]
    name = request.headers["name"]
    desc = request.headers["desc"]

    creator = validauth(authkey)
    if creator == "":
        return abort(401)

    gamedb.update({"name": name, "description": desc}, Query().id == gid and Query().creator == creator)
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
    newnode = {
        "name": name,
        "amount": int(amt),
        "id": gid,
        "parent": parent,
        "datecreated": time.time()
    }
    nodedb.insert(newnode)
    return gid

@app.route("/api/nodes/delete", methods=["POST"])
def deletenode():
    nid = request.headers["id"]
    parent = request.headers["parent"]

    creator = validauth(request.headers["authkey"])
    if creator == "":
        return abort(401)

    if (gamedb.contains(Query().id == parent and Query().creator == creator)):
        nodedb.remove(Query().id == nid)
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

    if (gamedb.contains(Query().id == parent and Query().creator == creator)):
        nodedb.update({"name": name, "amount": int(amt)}, Query().id == nid)
    return ""

@app.route("/api/recent/<int:amt>", methods=["GET"])
def recents(amt: int):
    allgames = gamedb.all()
    amt = min(len(allgames), amt)
    out = []
    
    for i in range(-1, -amt):
        out.append(allgames[i])

    return json.dumps(out)

def validauth(ak) -> str:
    creator = authkv.get(Query().key == ak)
    if creator == None:
        return ""
    return creator["value"]

def creategameid() -> str:
    out = createid()
    while gamedb.contains(Query().id == out):
        out = createid()
    return out

def createnodeid() -> str:
    out = createid()
    while nodedb.contains(Query().id == out):
        out = createid()
    return out

def createhash(usernm: str):
    out = createid()
    while hashkv.contains(Query().key == out):
        out = createid()
    hashkv.insert({ "key": out, "value": usernm})
    return out

def createauth(usernm: str):
    out = createid()
    while authkv.contains(Query().key == out):
        out = createid()
    authkv.insert({ "key": out, "value": usernm})
    return out

def createid():
    pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(pool, k=20))