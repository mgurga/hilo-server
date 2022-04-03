<script>
    import Nav from "../components/Nav.svelte";
</script>

<title>HiLo</title>
<Nav />
<main>
    <div id="menu">
        <h1>HiLo: Higher or Lower</h1>
        <p>Play and Create you own higher or lower games</p>
    </div>
</main>

<style>
    main {
        display: flex;
        justify-content: center;
        align-items: center;
        height: calc(100% - 64px); /* minus 5% to account for Nav bar */
    }

    #menu {
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
</style>