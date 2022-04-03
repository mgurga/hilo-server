<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let target: number = 0;
    export let num: number = 0;
    export let inc: boolean = true;

    function increment() {
        setTimeout(function() {
            if (num != target && inc) {
                num = num + 1;
                increment();
            } else {
                dispatch("finished")
            }
        }, 2000/target);
    }

    setTimeout(function() {
        increment()
    }, 100);
</script>

<h1>{num}</h1>