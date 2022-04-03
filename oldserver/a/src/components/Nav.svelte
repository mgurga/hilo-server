<script lang="ts">
    import { username, key } from '../stores.js';
    import IconButton from '@smui/icon-button';
    import Button from '@smui/button';
    import TopAppBar, { Row, Section, Title } from '@smui/top-app-bar';

    function logout() {
        $username = "";
        $key = "";
        window.location.href = "/login"
    }
</script>

<nav>
    <!-- <a href="/"><span>HiLo</span></a>
    <div id="floatright">
        {#if $key == ""}
        <a href="/login"><span>Login</span></a>
        {:else}
        <a href="/mygames"><span>My Games</span></a>
        <span style="padding-right: 0px"></span>
        <IconButton style="padding: 0" size="button" class="material-icons" on:click={logout}>logout</IconButton>
        {/if}
    </div> -->
    <TopAppBar
      variant="static"
      color='primary'>
      <Row>
        <Section>
          <Title on:click={() => {window.location.href = "/"}} style="cursor: pointer; user-select: none;">HiLo</Title>
        </Section>
        <Section align="end" toolbar>
            {#if $key != ""}
            <Button on:click={() => {window.location.href = "/mygames"}}>My Games</Button>
            <IconButton on:click={logout} class="material-icons" aria-label="Logout">logout</IconButton>
            {:else}
            <Button on:click={() => {window.location.href = "/login"}}>Login</Button>
            {/if}
        </Section>
      </Row>
    </TopAppBar>
</nav>