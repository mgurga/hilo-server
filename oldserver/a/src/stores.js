import { writable } from 'svelte/store';
import { browser } from "$app/env";

export const server_url = writable("http://localhost:8000");

export let username = writable("");
export let key = writable("");

if (browser) {
    username.set(JSON.parse(localStorage.getItem("user")) || "")
    key.set(JSON.parse(localStorage.getItem("key")) || "")
    username.subscribe((value) => localStorage.setItem("user", JSON.stringify(value)))
    key.subscribe((value) => localStorage.setItem("key", JSON.stringify(value)))
}