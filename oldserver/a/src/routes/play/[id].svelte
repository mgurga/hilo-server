<script lang="ts">
    import Dialog, { Title, Content, Actions } from "@smui/dialog";
    import { tweened } from 'svelte/motion';
    import { fade, fly } from 'svelte/transition';
    import Button, { Label } from '@smui/button';
    import Fab, { Icon } from '@smui/fab';
    import { onMount } from 'svelte';
    import { server_url } from '../../stores.js';
    import { page } from '$app/stores';
    import CountUp from './CountUp.svelte';

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
    let leftitem: GameNode = null;
    let rightitem: GameNode  = null;
    let nodelist: Array<GameNode>;
    let curnode: number = 0;
    let buttonsvisible = true;
    let showamounts = false;
    let outcome: boolean = null;
    let userchoice = "";
    let score = 0;
    let progress = 0;
    let colors = ["darkblue", "rgb(0, 0, 90)"];
    let mandatorydialog = false;
    let infodialog = false;

    onMount(() => {
        fetch(`${$server_url}/api/game/${$page.params.id}/info`, {"method": "GET"})
        .then((response) => response.json())
        .then((data) => {
            if (data.error == "invalid game") {
                alert("invalid game");
                window.location.href = "/";
            }
            gameinfo = data;
        })
        fetch(`${$server_url}/api/game/${$page.params.id}/nodes`, {"method": "GET"})
        .then((response) => response.json())
        .then((data) => {
            gamenodes = data;

            if (gamenodes.length >= 3) {
                nodelist = [gamenodes[(Math.random() * gamenodes.length) | 0]];
                let newitem = gamenodes[(Math.random() * gamenodes.length) | 0];
                for (var i = 0; i < 1000; i++) {
                    while (newitem.id == nodelist[nodelist.length - 1].id) {
                        newitem = gamenodes[(Math.random() * gamenodes.length) | 0];
                    }
                    nodelist = [...nodelist, newitem]
                }

                leftitem = nodelist[0];
                rightitem = nodelist[1];
                curnode = 2;
                infodialog = true;
            } else {
                mandatorydialog = true;
                buttonsvisible = false;
            }
        })
    })

    function decisionpressed(dir: string) {
        buttonsvisible = false;
        userchoice = dir;
        setTimeout(function() {
            showamounts = true;
        }, 1000)
    }

    function finishedcount() {
        if (userchoice == "higher") {
            outcome = rightitem.amount >= leftitem.amount;
        } else {
            outcome = rightitem.amount <= leftitem.amount;
        }
        if (outcome) {
            score = score + 1;
        }

        if (outcome) {
            setTimeout(function() {
                // showamounts = false;
                outcome = null;

                function increment() {
                    setTimeout(function() {
                        if (progress != 100) {
                            progress = progress + 1;
                            increment();
                        } else {
                            quickswitch();
                        }
                    }, 10);
                }

                increment();
            }, 3000)
        }
        // console.log(`${leftitem.amount} vs ${rightitem.amount} done counting, you ${outcome ? "WIN" : "LOSE"}`);
    }

    function quickswitch() {
        leftitem.amount = nodelist[curnode - 1].amount;
        leftitem.name = nodelist[curnode - 1].name;
        leftitem.id = nodelist[curnode - 1].id;
        rightitem.amount = nodelist[curnode].amount;
        rightitem.name = nodelist[curnode].name;
        rightitem.id = nodelist[curnode].id;
        curnode++;

        colors = [colors[1], colors[0]]
        progress = 0
        showamounts = false;
        buttonsvisible = true;
    }
</script>
<Dialog
    bind:open={mandatorydialog}
    scrimClickAction=""
    escapeKeyAction="">
    <Title id="mandatory-title">Error</Title>
    <Content id="mandatory-content">The game does not have enough items to play.</Content>
</Dialog>
<Dialog
    bind:open={infodialog}>
    <Title>{gameinfo == null ? "" : gameinfo.name} by {gameinfo == null ? "" : gameinfo.creator}</Title>
    <Content>{gameinfo == null ? "" : gameinfo.description}</Content>
    <Actions>
        <Button on:click={() => (infodialog = false)}><Label>Play</Label></Button>
    </Actions>
</Dialog>

<title>HiLo</title>
<main style="background-color: {colors[0]}">
    <div id="left" style="background-color: {colors[0]}">
        <h1>{leftitem == null ? "" : leftitem.name}</h1>
        {#if leftitem != null}
        <div class="amounts" transition:fade>
            <CountUp bind:num={leftitem.amount} inc={false}/>
        </div>
        {/if}
    </div>
    <div id="right" style="transform: translateX(-{progress}%); background-color: {colors[1]};">
        <h1>{rightitem == null ? "" : rightitem.name}</h1>
        {#if buttonsvisible}
        <div id="buttons" style="display: grid;" transition:fade>
            <Button variant="raised" style="background-color: green; margin-bottom: 10px" on:click={() => {decisionpressed("higher")}}>
                <Label>Higher</Label>
                <Icon class="material-icons">arrow_upward</Icon>
            </Button>
            <Button variant="raised" style="background-color: red;" on:click={() => {decisionpressed("lower")}}>
                <Label>Lower</Label>
                <Icon class="material-icons">arrow_downward</Icon>
            </Button>
        </div>
        {/if}
        {#if showamounts}
        <div class="amounts" in:fade>
            <CountUp on:finished={finishedcount} target={rightitem.amount} />
        </div>
        {/if}
    </div>
    <div id="outcome">
        {#if outcome != null}
        <div transition:fade>
            <Fab style="background-color: {outcome ? "green" : "red"}">
                <Icon class="material-icons">{outcome ? "check" : "close"}</Icon>
            </Fab>
        </div>
        {/if}
    </div>
    <h1 style="z-index: 6; position: absolute; color: white; margin-top: 5px">{score}</h1>
</main>

<style>
    h1 {
        font-size: 50px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        justify-content: center;
    }

    #outcome {
        position: absolute;
        z-index: 5;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        top: calc((100% / 2) - 5%);
    }

    #left, #right {
        width: 50%;
        margin: 0;
        height: 100%;
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }

    #left > * {
        display: flex;
    }

    main {
        display: flex;
        justify-content: center;
        height: 100%; /* minus 5% to account for Nav bar */
    }
</style>