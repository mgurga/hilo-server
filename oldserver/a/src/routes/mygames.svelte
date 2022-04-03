<script lang="ts">
    import Button from '@smui/button';
    import CircularProgress from '@smui/circular-progress';
    import Fab, { Icon } from '@smui/fab';
    import { username, key, server_url } from '../stores.js';
    import Nav from "../components/Nav.svelte";
    import { onMount } from 'svelte';

    type Game = {
        creator: string;
        id: string;
        name: string;
        description: string;
        datecreated: number;
    }

    let usergames: Array<Game> = null;

    onMount(() => {
        if ($username == "" || $key == "") {
            alert("you are not signed in");
            window.location.href = "/login";
        }

        fetch(`${$server_url}/api/${$username}/games`, {"method": "GET"})
        .then((response) => response.json())
        .then((data) => {
            usergames = data;
        })
    })

    function createGame() {
        fetch(`${$server_url}/api/games/create`, {"method": "GET", "headers" : { "authkey": $key }})
        .then((response) => response.json())
        .then((data) => {
            usergames = [...usergames, data]
        })
    }

    function deleteGame(id: string, index: number) {
        fetch(`${$server_url}/api/games/delete`, {"method": "POST", "headers" : { "authkey": $key, "id": id }})
        usergames = [...usergames.slice(0, index), ...usergames.slice(index + 1)];
    }
</script>

<Nav />
<main>
    <div id="menu">
        <div id="gamesheader">
            <h2 class="header">My Games</h2>
            <div style="float: right;">
                <Fab color="primary" on:click={createGame} mini>
                    <Icon class="material-icons">add</Icon>
                </Fab>
            </div>
        </div>
        <div id="usergames">
            {#if usergames != null}
            {#each usergames as g, i}
            <div class="gamecard">
                <div style="width: fit-content; display: inline-block;">
                    <h2 class="gamecardinfo">{g.name}</h2>
                    <br>
                    <br>
                    <p class="gamecardinfo">{g.description}</p>
                </div>
                <div style="display: block;">
                    <Button style="float: right;" on:click={() => {deleteGame(g.id, i)}}>Delete</Button>
                    <Button style="float: right;" on:click={() => {window.location.href = `/editor/${g.id}`}}>Edit</Button>
                </div>
            </div>
            {/each}
            {:else}
            <div style="display: flex; justify-content: center; padding-top: 20px">
                <CircularProgress style="height: 40px; width: 40px;" indeterminate />
            </div>
            {/if}
        </div>
    </div>
</main>

<style>
    .gamecardinfo {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: inline;
        margin: 0;
        width: fit-content;
    }

    #usergames {
        width: 100%;
    }

    .gamecard {
        display: inline-block;
        width: 97%;
        padding: 10px;
        border: 1px solid black;
        border-top: 0;
    }

    #gamesheader {
        border-bottom: 2px solid black;
        padding: 0 10px 20px 10px;
    }

    .header {
        margin: 0;
        width: fit-content;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: inline;
        font-size: 30px;
    }

    main {
        display: flex;
        justify-content: center;
        /* align-items: center; */
        height: calc(100% - 64px) /* minus 5% to account for Nav bar */
    }

    #menu {
        margin-top: 20px;
        padding: 10px;
        width: 70%;
        /* border: 1px solid grey; */
        /* height: 50%; */
    }
</style>