<script>
  import { page } from "$app/stores";
  import {derived} from 'svelte/store';
  import { slide } from "svelte/transition";
  import "../app.css";
  import Page from "./contact/+page.svelte";

  function handleClickOutside(element) {
    // thanks to https://svelte.dev/repl/ae791a22dcd14f40bc56d12f2c63c002?version=4.2.0 !
    function handleClick(e) {
      if (!element.contains(e.target)) {
        element.dispatchEvent(new CustomEvent("outsideclick"));
      }
    }
    window.addEventListener("click", handleClick);

    return {
      destroy() {
        window.removeEventListener("click", handleClick);
      },
    };
  }

  const path = derived(page, ($page) => $page.url.pathname);
  let showMediaDropdown = false;
  let hideMediaDropdown = true;
  const toggleMediaDropdown = () => {
    showMediaDropdown = !showMediaDropdown;
    hideMediaDropdown = !hideMediaDropdown;
  };
  const handleOutsideMediaClick=()=>{
    showMediaDropdown = false;
    hideMediaDropdown = true;
  }
</script>

<div class="container max-w-full">
  <nav>
    <a href="/home" class:current={"/home" === $path}>Home</a>
    <a href="/contact" class:current={"/contact" === $path}>Contact</a>
    <a href="/projects" class:current={$path.startsWith("/projects")}>Projects</a>
    <a href="/blurbs" class:current={$path.startsWith("/blurbs")}>Blurbs</a>
    <div
      class="relative inline-block text-left group"
      on:click={toggleMediaDropdown}
      on:keydown={toggleMediaDropdown}
      use:handleClickOutside
      on:outsideclick={handleOutsideMediaClick}
      role="menu"
      tabindex="0"
    >
      <div class:showMediaDropdown 
      class:current={$path.startsWith("/media")}
        tabindex="-1"
      >
        <div
          class="group inline-flex w-full justify-center gap-x-1.5 bg-333 px-3 py-2 hover:underline"
          id="menu-button"
          aria-expanded="true"
          aria-haspopup="true"
        >
          My Media
          <svg
            class="-mr-1 h-5 w-5 text-gray-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
              clip-rule="evenodd"
            />
          </svg>
          <div
            class:showMediaDropdown
            class:hideMediaDropdown
            class="menuholder outline-dotted transition duration-100 top-5 absolute right-0 mt-2 w-56 rounded-md bg-black shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
            role="menu"
            aria-orientation="vertical"
            aria-labelledby="menu-button"
            tabindex="0"
          >
            <a
              href="/media/movies_and_tv"
              class="text-white-700 block px-4 py-2 text-sm"
              role="menuitem"
              tabindex="0">Movies & TV</a
            >
            <a
              href="/media/youtube"
              class="text-white-700 block px-4 py-2 text-sm"
              role="menuitem"
              tabindex="0">Youtube</a
            >
            <a
              href="/media/music"
              class="text-white-700 block px-4 py-2 text-sm"
              role="menuitem"
              tabindex="0">Music</a
            >
            <a
              href="/media/podcasts"
              class="text-white-700 block px-4 py-2 text-sm"
              role="menuitem"
              tabindex="0">Podcasts</a
            >
            <a
              href="/media/books"
              class="text-white-700 block px-4 py-2 text-sm"
              role="menuitem"
              tabindex="0">Books</a
            >
          </div>
        </div>
      </div>

    </div>
  </nav>

  <div class="content">
    <slot />
  </div>
</div>

<style>
  .showMediaDropdown {
    display: block;
  }

  .hideMediaDropdown {
    display: none;
  }

  .container {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  .content {
    flex: 1;
    padding: 20px;
    background-color: #f0f0f0;
  }

  nav {
    display: flex;
    justify-content: space-around;
    align-items: center;
    background-color: #333;
    color: #fff;
    padding: 1rem;
  }

  nav a {
    color: #fff;
    text-decoration: none;
  }

  nav a:hover {
    text-decoration: underline;
  }

  nav a.current,div.current {
    color: bisque;
  }
  .menuholder {
    background-color: #333;
  }
</style>
