<script>
  import { browser } from "$app/environment";
    import { persist, createLocalStorage } from "@macfja/svelte-persistent-store";
    import { writable } from "svelte/store";
    import {slide} from "svelte/transition";
    let items;
    const arr = Array.from({ length: 100 }, (_, i) => {
      return {
        index: i,
        expanded: false,
        className: "collapsed",
        text1: "Lorem ipsum dolor sit amet, consectetur adipiscing elit",
        text2:
          "Sed non risus. Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor.",
        text3:
          "Cras elementum ultrices diam. Maecenas ligula massa, varius a, semper congue, euismod non, mi.",
      };
    });
    if(browser){
        items = persist(writable(arr), createLocalStorage(), "items");
    }
  
    // @ts-ignore
    const setItemValue = (index, value) => {
      items.update((items) => {
        items[index] = value;
        return items;
      });
    };
  
  
  </script>
  
  <h1>Welcome to SvelteKit</h1>
  
  {#each $items as item}
    <div>
      <!-- <a href="#" on:click={() => goto(`/hello/`)}>Page {item.index + 1}</a> -->
      <a href="/hello/{item.index}">Page {item.index + 1}</a>
      <button
        on:click={() => {
          setItemValue(item.index, {
            ...item,
            expanded: !item.expanded,
            className: item.expanded ? "collapsed" : "expanded",
          });
        }}
      >
        {item.expanded ? "Collapse" : "Expand"}</button
      >
  
      {#if item.expanded}
        <div
          transition:slide={{ duration: 50 }}
        class={item.className}>
          <p>{item.text1}</p>
          <p>{item.text2}</p>
          <p>{item.text3}</p>
        </div>
      {/if}
    </div>
  {/each}
  
  <style>
  </style>
  