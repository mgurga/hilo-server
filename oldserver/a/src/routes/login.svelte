<script lang="ts">
    import Tab, { Label } from '@smui/tab';
    import TabBar from '@smui/tab-bar';
    import Nav from "../components/Nav.svelte";
    import { username, key, server_url } from '../stores.js';
    import { onMount } from 'svelte';
    import Button from '@smui/button';

    // console.log("server url: " + $server_url);

    let error = "";
    let success = "";
    let active = "Login";

    onMount(() => {
        const url = window.location.href
        if (url.includes("#")) {
            let hash = url.split("#")[1];
            let user = url.split("#")[2];
            if (hash == "incorrect") {
                error = "user does not exist";
            } else if(hash == "exists") {
                error = "username is already registered";
            } else if(hash == "registered") {
                success = "successfully registered, now login";
            } else {
                fetch(`${$server_url}/api/authkey/${hash}/${user}`, {"method": "GET"})
                .then((response) => response.text())
                .then((data) => {
                    if (data.length == 20) {
                        $key = data;
                        $username = user;
                        success = "successfully logged in";
                        // console.log(data);
                        window.history.pushState({}, document.title, "/" + "login");
                    }
                    if (data == "invalid hash")
                        alert("invalid hash, try signing in again")
                })
            }
        }
    });
</script>

<title>{active == "Login" ? "Login" : "Register"}</title>
<Nav />
<main>
    <div id="menu">
        <TabBar tabs={['Login', 'Register']} let:tab bind:active>
            <Tab {tab}>
                <Label>{tab}</Label>
            </Tab>
        </TabBar>

        <form action="{$server_url}/api/{active == "Login" ? "signin" : "register"}">
            <!-- <h2 style="width: auto; text-align: center;">{active == "Login" ? "Login" : "Register"}</h2> -->
            <br>
            <p>Username</p>
            <input type="text" name="user">
            <br>
            <p>Password</p>
            <input type="password" name="pass">
            <br>
            <Button style="margin: 0 auto; display: block;" type="submit">Submit</Button>
        </form>

        <p style="color: red;">{error}</p>
        <p style="color: green;">{success}</p>
    </div>
</main>

<style>
    main {
        display: flex;
        justify-content: center;
        align-items: center;
        height: calc(100% - 64px);
    }

    p {
        margin: 0;
        color: rgb(43, 43, 43);
        width: 100%;
        text-align: center;
    }

    input {
        margin: 0 auto;
        display: block;
    }

    #menu {
        padding: 10px;
        border: 1px solid grey;
        width: 30%;
        /* height: 50%; */
    }
</style>