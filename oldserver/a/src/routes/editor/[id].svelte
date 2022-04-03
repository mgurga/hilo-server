<script lang="ts">
    import { username, key, server_url } from '../../stores.js';
    import Nav from "../../components/Nav.svelte";
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import Dialog, { Title, Actions } from "@smui/dialog";
    import Button, { Label } from '@smui/button';
    import Textfield from '@smui/textfield';
    import CircularProgress from '@smui/circular-progress';
    import LayoutGrid, { Cell } from '@smui/layout-grid';
    import IconButton from '@smui/icon-button';
    import Fab, { Icon } from '@smui/fab';
    import { Section } from '@smui/top-app-bar';
    import Tooltip, { Wrapper } from '@smui/tooltip';
    // console.log("editing: " + $page.params.id)

    type Game = {
        creator: string;
        id: string;
        name: string;
        description: string;
        datecreated: number;
    }

    type GameNode = {
        name: string;
        amount: number;
        id: string;
        parent: string;
    }

    let gameinfo: Game = null;
    let gamenodes: Array<GameNode> = [];
    let open = false;
    let newnodemenu = false;
    let newName = "";
    let newDesc = "";
    let newAmount = 0;
    let editnodemenu = false;
    let editingindex = 0;

    onMount(() => {
        verifylogin();
        fetch(`${$server_url}/api/game/${$page.params.id}/info`, {"method": "GET"})
        .then((response) => response.json())
        .then((data) => {
            gameinfo = data;
        })
        fetch(`${$server_url}/api/game/${$page.params.id}/nodes`, {"method": "GET"})
        .then((response) => response.json())
        .then((data) => {
            gamenodes = data;
        })
    })

    function changename() {
        open = true;
        editnodemenu = false
        newName = gameinfo.name;
        newDesc = gameinfo.description;
    }

    function savename() {
        open = false;
        verifylogin();
        fetch(`${$server_url}/api/games/info`, 
            {"method": "POST", "headers": {"authkey": $key, "id": $page.params.id, "name": newName, "desc": newDesc}})
            .then(() => {
                gameinfo.name = newName;
                gameinfo.description = newDesc;
            })
    }

    function verifylogin() {
        if ($username == "" || $key == "") {
            alert("you are not signed in");
            window.location.href = "/login";
        }
    }

    function newnode() {
        newnodemenu = true;
        editnodemenu = false
        newName = "";
        newAmount = 0;
    }

    function createnode() {
        let newgn: GameNode = {
            name: newName,
            amount: newAmount,
            parent: $page.params.id,
            id: ""
        };
        fetch(`${$server_url}/api/nodes/create`, 
            {"method": "GET", "headers" : { "authkey": $key, "name": newgn.name, "amount": newgn.amount.toString(), "parent": newgn.parent }})
        .then((response) => response.text())
        .then((data) => {
            if (data == "") {
                verifylogin();
            }
            newgn.id = data;
            gamenodes = [...gamenodes, newgn];
        })
    }

    function deletenode(nodeid: string, index: number) {
        fetch(`${$server_url}/api/nodes/delete`, 
            {"method": "POST", "headers" : { "authkey": $key, "id": nodeid, "parent": gamenodes[index].parent }});
        gamenodes = [...gamenodes.slice(0, index), ...gamenodes.slice(index + 1)];
    }

    function editnode(index: number) {
        newName = gamenodes[index].name
        newAmount = gamenodes[index].amount
        editnodemenu = true
        newnodemenu = true
        editingindex = index
    }

    function saveedits() {
        fetch(`${$server_url}/api/nodes/edit`, {"method": "POST", "headers" :
        { "authkey": $key, "name": newName, "amount": newAmount.toString(), "parent": gamenodes[editingindex].parent, "id": gamenodes[editingindex].id}})
        gamenodes[editingindex].name = newName;
        gamenodes[editingindex].amount = newAmount;
    }

    function play() {

    }
</script>

<title>Game Editor</title>
<Nav />
<main>
    <div id="menu">
        <div id="gamebanner">
            {#if gameinfo == null}
            <div style="display: flex; justify-content: center">
                <CircularProgress style="height: 32px; width: 32px;" indeterminate />
            </div>
            {:else}
            <div>
                <h1 on:click={changename} class="gameinfotext">{gameinfo.name}</h1>
                <br>
                <br>
                <p on:click={changename} class="gameinfotext">{gameinfo.description}</p>
            </div>
            
            <div style="grid-column-start: 2; grid-row-start: 1; text-align:right">
                <Wrapper>
                    <Fab color="primary" href="/play/{$page.params.id}">
                        <Icon class="material-icons">play_arrow</Icon>
                    </Fab>
                    <Tooltip>Play</Tooltip>
                </Wrapper>
            </div>
            {/if}
        </div>
        <div id="gamenodes">
            <LayoutGrid>
                {#each gamenodes as node, i}
                <Cell span={4}>
                    <div class="nodecell">
                        <Section align="start">
                            <div style="display: inline; padding-left: 10px">
                                <Title alt={node.name} size={10} style="padding: 0; display: flex;">{node.name}</Title>
                                <Label style="padding: 0; margin: 0;">{node.amount}</Label>
                            </div>
                        </Section>
                        <Section align="end">
                            <IconButton class="material-icons" on:click={() => {editnode(i)}}>edit</IconButton>
                            <IconButton class="material-icons" on:click={() => {deletenode(node.id, i)}}>delete</IconButton>
                        </Section>
                    </div>
                </Cell>
                {/each}
                <Cell span={4}>
                    <div class="nodecell createcell" on:click={newnode}>
                        <Icon class="material-icons">add</Icon>
                    </div>
                </Cell>
            </LayoutGrid>
        </div>
    </div>
</main>
<Dialog bind:open>
    <Title>Rename</Title>
    <Textfield bind:value={newName} label="Name" />
    <br>
    <Textfield textarea bind:value={newDesc} label="Description" />
    <Actions>
        <Button on:click={savename}><Label>Save</Label></Button>
    </Actions>
</Dialog>
<Dialog bind:open={newnodemenu}>
    <Title>{editnodemenu ? "Edit" : "New"} Node</Title>
    <Textfield bind:value={newName} label="Name" />
    <br>
    <Textfield type="number" bind:value={newAmount} label="Amount" />
    <Actions>
        <Button on:click={() => {editnodemenu ? saveedits() : createnode()}}><Label>{editnodemenu ? "Save" : "Add"}</Label></Button>
    </Actions>
</Dialog>

<style>
    .nodecell {
        height: 70px;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--mdc-theme-secondary, #333);
        color: var(--mdc-theme-on-secondary, #fff);
        cursor: pointer;
    }

    .createcell {
        background-color: var(--mdc-theme-secondary, rgb(38, 197, 38));
        color: var(--mdc-theme-on-secondary, #fff);
    }

    .gameinfotext {
        margin: 0;
        cursor: pointer;
        user-select: none;
        width: fit-content;
        display: inline-block;
    }

    #gamebanner {
        background-color: white;
        color: black;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 10px 10px 15px 10px;
        border-radius: 5px;
        border: 1px solid black;
        display: grid;
    }

    main {
        display: flex;
        justify-content: center;
        height: calc(100% - 64px); /* minus 5% to account for Nav bar */
    }

    #menu {
        margin-top: 0;
        padding: 10px;
        width: 70%;
    }
</style>