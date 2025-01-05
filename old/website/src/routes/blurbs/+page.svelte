
<script>

    const blurbs = [
        {'title':'hi',slug:'hello-world'},
        {'title':'lorem',slug:'lorem-ipsum'},
        {'title':'foo',slug:'foo-bar'},
    ]
</script>

<div>
    {#each blurbs as blurb}
        <a class="hover:underline visited:text-blue-600" href="/blurbs/{blurb.slug}">{blurb.title}</a>
        <br>
    {/each}


</div>