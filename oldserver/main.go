package main

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"github.com/kelindar/column"

	bolt "go.etcd.io/bbolt"
)

var boltdb *bolt.DB
var accountdb, gamesdb, gamenodesdb *column.Collection
var accdst, gdst, gndst *os.File

func main() {
	os.Mkdir("db", 0777)
	boltdb, _ = bolt.Open("sessions.db", 0600, nil)
	boltdb.Update(func(tx *bolt.Tx) error {
		tx.CreateBucket([]byte("authkey"))
		tx.CreateBucket([]byte("hashes"))
		return nil
	})

	accountdb = column.NewCollection()
	accountdb.CreateColumn("username", column.ForString())
	accountdb.CreateColumn("password", column.ForString())
	accountdb.CreateColumn("datecreated", column.ForInt64())

	gamesdb = column.NewCollection()
	gamesdb.CreateColumn("creator", column.ForString()) // username
	gamesdb.CreateColumn("id", column.ForString())
	gamesdb.CreateColumn("name", column.ForString())
	gamesdb.CreateColumn("description", column.ForString())
	gamesdb.CreateColumn("datecreated", column.ForInt64())

	gamenodesdb = column.NewCollection()
	gamenodesdb.CreateColumn("name", column.ForString())
	gamenodesdb.CreateColumn("amount", column.ForInt64())
	gamenodesdb.CreateColumn("id", column.ForString())
	gamenodesdb.CreateColumn("parent", column.ForString()) // game id
	gamenodesdb.CreateColumn("datecreated", column.ForInt64())

	accdst, err := os.Create("db/accounts.bin")
	if err != nil {
		println("cannot create account.bin: %v", err)
		// panic(err)
	}
	gdst, err := os.Create("db/games.bin")
	if err != nil {
		println("cannot open games, creating the file")
		// panic(err)
	}
	gndst, err := os.Create("db/gamenodes.bin")
	if err != nil {
		println("cannot open game nodes, creating the file")
		// panic(err)
	}

	if fi, _ := os.Stat(accdst.Name()); fi.Size() != 0 {
		err = accountdb.Restore(accdst)
		if err != nil {
			println(err.Error())
		}
	}
	println("restored " + fmt.Sprint(accountdb.Count()) + " accounts")
	gamesdb.Restore(gdst)
	println("restored " + fmt.Sprint(gamesdb.Count()) + " games")
	gamenodesdb.Restore(gndst)
	println("restored " + fmt.Sprint(gamenodesdb.Count()) + " game nodes")

	// if err := accountdb.Snapshot(accdst); err != nil {
	// 	println("cannot create snapshot: '" + err.Error() + "'")
	// }
	gamesdb.Snapshot(gdst)
	gamenodesdb.Snapshot(gndst)

	r := chi.NewRouter()
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedHeaders: []string{"authkey", "id", "name", "desc", "amount", "parent"},
	}))
	r.Use(middleware.Logger)
	r.Use(putConversion)

	r.Route("/list", func(r chi.Router) {
		r.Get("/games", listgames) // returns list of games
		r.Get("/users", listusers) // returns list of users
		r.Get("/nodes", listnodes) // returns list of node
		//r.Get("/keyring", listauths) // returns list of valid authkeys (hide this in prod)
	})
	r.Route("/api", func(r chi.Router) {
		r.Get("/signin", signin)                    // returns redirect (probably change to a Post)
		r.Get("/authkey/{hash}/{user}", getauthkey) // returns an authkey after registering
		r.Get("/register", register)                // returns redirect (probably change to a Post)
		r.Get("/games/create", creategame)          // returns game id
		r.Post("/games/delete", deletegame)
		r.Get("/{user}/games", usergames)      // returns all games a user has made
		r.Get("/game/{id}/info", gameid)       // returns game json data
		r.Get("/game/{id}/nodes", gamenodesid) // returns game json data
		r.Post("/games/info", setnamedesc)
		r.Get("/nodes/create", createnode) // returns node id
		r.Post("/nodes/delete", deletenode)
		r.Post("/nodes/edit", editnode)
	})

	println("started chi api on :8000")
	log.Fatal(http.ListenAndServe(":8000", r))
}

func gamenodesid(w http.ResponseWriter, r *http.Request) {
	var id = chi.URLParam(r, "id")
	var out = "["

	gamenodesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("parent", func(v interface{}) bool { return v == id }).Range(func(i uint32) {
			name, _ := txn.String("name").Get()
			amount, _ := txn.Int64("amount").Get()
			id, _ := txn.String("id").Get()
			parent, _ := txn.String("parent").Get()
			created, _ := txn.Int64("datecreated").Get()

			out += `{
	"name": "` + name + `",
	"amount": ` + fmt.Sprint(amount) + `,
	"id": "` + id + `",
	"parent": "` + parent + `",
	"datecreated": ` + fmt.Sprint(created) + `
},`
		})
		return nil
	})
	if out[len(out)-1] == byte(',') {
		out = out[0 : len(out)-1]
	}
	out += "]"
	w.Write([]byte(out))
}

func editnode(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var parent = r.Header.Get("parent")
	var nid = r.Header.Get("id")
	var name = r.Header.Get("name")
	var amount = r.Header.Get("amount")

	var creator = validauth(authkey)
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		w.Write([]byte(`invalid authkey`))
		return
	}

	var owner = false
	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == parent }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			owner = creatorval == creator
		})
		return nil
	})
	if owner == false {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	gamenodesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == nid }).Range(func(i uint32) {
			amt, _ := strconv.Atoi(amount)
			txn.String("name").Set(name)
			txn.Int64("amount").Set(int64(amt))
		})
		return nil
	})
	// gamenodesdb.Snapshot(gndst)
}

func createnode(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var name = r.Header.Get("name")
	var amount, _ = strconv.Atoi(r.Header.Get("amount"))
	var parent = r.Header.Get("parent")

	var creator = validauth(authkey)
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		w.Write([]byte(`invalid authkey`))
		return
	}

	var gid = genid()
	gamenodesdb.InsertObject(map[string]interface{}{
		"name":        name,
		"amount":      amount,
		"id":          gid,
		"parent":      parent,
		"datecreated": time.Now().Unix(),
	})

	w.Write([]byte(gid))
	// gamenodesdb.Snapshot(gndst)
}

func listnodes(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Total of " + fmt.Sprint(gamenodesdb.Count()) + " elements\n"))
	gamenodesdb.Query(func(txn *column.Txn) error {
		txn.With("id").Range(func(i uint32) {
			name, _ := txn.String("name").Get()
			amount, _ := txn.Int64("amount").Get()
			id, _ := txn.String("id").Get()
			parent, _ := txn.String("parent").Get()
			created, _ := txn.Int64("datecreated").Get()

			w.Write([]byte(fmt.Sprintf("name: '%s' amount:'%d' id:'%s' parent: '%s' created: '%d'\n", name, amount, id, parent, created)))
		})

		return nil
	})
}

func deletenode(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var nid = r.Header.Get("id")
	var parent = r.Header.Get("parent")

	var creator = validauth(authkey)
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	var owner = false
	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == parent }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			owner = creatorval == creator
		})
		return nil
	})
	if owner == false {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	gamenodesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == nid }).Range(func(i uint32) {
			fmt.Printf("deleted game node num: %v\n", txn.DeleteAt(i))
		})
		return nil
	})
	// gamenodesdb.Snapshot(gndst)
}

func setnamedesc(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var gid = r.Header.Get("id")
	var name = r.Header.Get("name")
	var desc = r.Header.Get("desc")

	var creator = validauth(authkey)
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == gid }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()

			if creatorval == creator {
				txn.String("name").Set(name)
				txn.String("description").Set(desc)
			}
		})

		return nil
	})
	// gamesdb.Snapshot(gdst)
}

func gameid(w http.ResponseWriter, r *http.Request) {
	var id = chi.URLParam(r, "id")
	var found = false
	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("id", func(v interface{}) bool { return v == id }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			nameval, _ := txn.String("name").Get()
			idval, _ := txn.String("id").Get()
			dateval, _ := txn.Int64("datecreated").Get()
			descval, _ := txn.String("description").Get()

			w.Write([]byte(`{
	"creator": "` + creatorval + `",
	"id": "` + idval + `",
	"name": "` + nameval + `",
	"description": "` + descval + `",
	"datecreated": ` + fmt.Sprint(dateval) + `
}`))
			found = true
		})

		return nil
	})
	if !found {
		w.Write([]byte(`{"error": "invalid game"}`))
	}
}

func usergames(w http.ResponseWriter, r *http.Request) {
	var creator = chi.URLParam(r, "user")
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	var out string = "["
	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("creator", func(v interface{}) bool { return v == creator }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			nameval, _ := txn.String("name").Get()
			idval, _ := txn.String("id").Get()
			dateval, _ := txn.Int64("datecreated").Get()
			descval, _ := txn.String("description").Get()

			if creatorval == creator {
				out += `{
	"creator": "` + creatorval + `",
	"id": "` + idval + `",
	"name": "` + nameval + `",
	"description": "` + descval + `",
	"datecreated": ` + fmt.Sprint(dateval) + `
},`
			}
		})

		return nil
	})
	if out[len(out)-1] == byte(',') {
		out = out[0 : len(out)-1]
	}
	out += "]"
	w.Write([]byte(out))
}

func listusers(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Total of " + fmt.Sprint(accountdb.Count()) + " elements\n"))
	accountdb.Query(func(txn *column.Txn) error {
		usercol := txn.String("username")
		datecol := txn.Int64("datecreated")

		txn.With("username").Range(func(i uint32) {
			userval, _ := usercol.Get()
			dateval, _ := datecol.Get()

			w.Write([]byte(fmt.Sprintf("username: '%s' password:'*' dateval:'%d'\n", userval, dateval)))
		})

		return nil
	})
}

func listauths(w http.ResponseWriter, r *http.Request) {
	boltdb.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("authkey"))
		b.ForEach(func(k, v []byte) error {
			w.Write([]byte(fmt.Sprintf("authkey: '%s' user: '%s'\n", k, v)))
			return nil
		})
		return nil
	})
}

func listgames(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Total of " + fmt.Sprint(gamesdb.Count()) + " elements\n"))
	gamesdb.Query(func(txn *column.Txn) error {
		txn.With("creator").Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			nameval, _ := txn.String("name").Get()
			idval, _ := txn.String("id").Get()

			w.Write([]byte(fmt.Sprintf("creator: '%s' name:'%s' id:'%s'\n", creatorval, nameval, idval)))
		})

		return nil
	})
}

func deletegame(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var id = r.Header.Get("id")

	var creator = validauth(authkey)
	if creator == "" {
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		return
	}

	gamesdb.Query(func(txn *column.Txn) error {
		txn.WithValue("creator", func(v interface{}) bool { return v == creator }).Range(func(i uint32) {
			creatorval, _ := txn.String("creator").Get()
			idval, _ := txn.String("id").Get()

			if creatorval == creator && idval == id {
				fmt.Printf("deleted game index num: %v\n", txn.DeleteAt(i))
			}
		})

		return nil
	})
	// gamesdb.Snapshot(gdst)
}

func creategame(w http.ResponseWriter, r *http.Request) {
	var authkey = r.Header.Get("authkey")
	var creator = validauth(authkey)
	var gid = genid()

	println(creator + " created a new game")

	if creator == "" {
		println("cannot create game b/c invalid authkey")
		http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
		w.Write([]byte(`{"error": "invalid authkey"}`))
	}

	gamesdb.InsertObject(map[string]interface{}{
		"creator":     creator,
		"id":          gid,
		"name":        "New Game",
		"description": "Newly created game by " + creator,
		"datecreated": time.Now().Unix(),
	})
	// gamesdb.Snapshot(gdst)

	w.Write([]byte(`{
	"creator": "` + creator + `",
	"id": "` + gid + `",
	"name": "New Game",
	"description": "Newly created game by ` + creator + `",
	"datecreated": ` + fmt.Sprint(time.Now().Unix()) + `
}`))
}

func getauthkey(w http.ResponseWriter, r *http.Request) {
	var hash string = chi.URLParam(r, "hash")
	var user string = chi.URLParam(r, "user")
	var exists bool = false
	println("generating authkey for " + user)
	boltdb.View(func(tx *bolt.Tx) error {
		res := tx.Bucket([]byte("hashes")).Get([]byte(hash))
		if string(res) == user {
			exists = true
		}
		return nil
	})
	if exists {
		var authkey = createauthkey(user)
		w.Write([]byte(authkey))

		boltdb.Update(func(tx *bolt.Tx) error {
			b := tx.Bucket([]byte("hashes"))
			b.Delete([]byte(hash))
			return nil
		})
	}
}

func signin(w http.ResponseWriter, r *http.Request) {
	println("signing in user: '" + r.FormValue("user") + "' pass: '" + r.FormValue("pass") + "'")
	var exists bool = false

	accountdb.Query(func(txn *column.Txn) error {
		txn.With("username").Range(func(i uint32) {
			userval, _ := txn.String("username").Get()
			passval, _ := txn.String("password").Get()

			if userval == r.FormValue("user") && passval == r.FormValue("pass") {
				exists = true
			}
		})

		return nil
	})

	if exists {
		var hash = createhash(r.FormValue("user"))
		http.Redirect(w, r, "http://localhost:3000/login#"+hash+"#"+r.FormValue("user"), http.StatusTemporaryRedirect)
	} else {
		http.Redirect(w, r, "http://localhost:3000/login#incorrect", http.StatusTemporaryRedirect)
	}
}

func register(w http.ResponseWriter, r *http.Request) {
	println("registering user: '" + r.FormValue("user") + "' pass: '" + r.FormValue("pass") + "'")
	var exists = false
	accountdb.Query(func(txn *column.Txn) error {
		txn.With("username").Range(func(i uint32) {
			userval, _ := txn.String("username").Get()

			if userval == r.FormValue("user") {
				exists = true
			}
		})

		return nil
	})

	if !exists {
		accountdb.InsertObject(map[string]interface{}{
			"username":    r.FormValue("user"),
			"password":    r.FormValue("pass"),
			"datecreated": time.Now().Unix(),
		})

		// println("snapshotting " + fmt.Sprint(accountdb.Count()) + " account")
		// if err := accountdb.Snapshot(accdst); err != nil {
		// 	println("cannot create snapshot: '" + err.Error() + "'")
		// }
		http.Redirect(w, r, "http://localhost:3000/login#registered", http.StatusTemporaryRedirect)
	} else {
		http.Redirect(w, r, "http://localhost:3000/login#exists", http.StatusTemporaryRedirect)
	}
}

func createhash(user string) string {
	var hash = genid()
	boltdb.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("hashes"))
		err := b.Put([]byte(hash), []byte(user))
		if err != nil {
			panic(err)
		}
		return nil
	})
	return hash
}

func createauthkey(user string) string {
	var key = genid()
	boltdb.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("authkey"))
		b.Put([]byte(key), []byte(user))
		return nil
	})
	return key
}

func validauth(authkey string) string {
	var user string = ""
	boltdb.View(func(tx *bolt.Tx) error {
		res := tx.Bucket([]byte("authkey")).Get([]byte(authkey))
		user = string(res)
		return nil
	})
	return user
}

func genid() string {
	var val string = randomString(20)
	for idused(val) {
		val = randomString(20)
	}
	return val
}

func idused(id string) bool {
	var exists bool = false
	gamesdb.Query(func(txn *column.Txn) error {
		txn.With("id").Range(func(i uint32) {
			gid, _ := txn.String("id").Get()
			if gid == id {
				exists = true
			}
		})

		return nil
	})
	if exists {
		return true
	}
	gamenodesdb.Query(func(txn *column.Txn) error {
		txn.With("id").Range(func(i uint32) {
			gid, _ := txn.String("id").Get()
			if gid == id {
				exists = true
			}
		})

		return nil
	})
	if exists {
		return true
	}
	boltdb.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("authkey"))
		out := b.Get([]byte(id))
		if out != nil {
			exists = true
		}
		return nil
	})
	if exists {
		return true
	}
	boltdb.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("hashes"))
		out := b.Get([]byte(id))
		if out != nil {
			exists = true
		}
		return nil
	})
	return exists
}

func putConversion(next http.Handler) http.Handler {
	return http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			if r.Method == "POST" {
				r.ParseForm()
				if r.Form["_method"] != nil && r.FormValue("_method") == "PUT" {
					r.Method = "PUT"
				}
			}
			next.ServeHTTP(w, r)
		})
}

func randomInt(min, max int) int {
	return min + rand.Intn(max-min)
}

func randomString(len int) string {
	keychars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	bytes := make([]byte, len)
	for i := 0; i < len; i++ {
		bytes[i] = keychars[rand.Intn(62)]
	}
	return string(bytes)
}
