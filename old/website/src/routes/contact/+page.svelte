<script>
  import GithubIcon from '$lib/icons/github-svg.svelte'
  import LinkedInIcon from '$lib/icons/linkedin-svg.svelte'
  import TwitterIcon from '$lib/icons/twitter-svg.svelte'
  import GmailSvg from '$lib/icons/gmail-svg.svelte';
  import PhoneILSvg from '$lib/icons/phone-il-svg.svelte'
  import PhoneUsaSvg from '$lib/icons/phone-usa-svg.svelte';
</script>

<div class="contact-container">
  <div class="contact-details">
    <h1>Contact Information</h1>
    <p>Name: Shmuel Kamensky</p>
    
    <ul class="flex space-x-2.5">
        <li>
            <a href="https://www.github.com/skamensky"><GithubIcon></GithubIcon></a>
        </li>
        <li>
            <a href="https://www.linkedin.com/in/shmuelkamensky"><LinkedInIcon></LinkedInIcon></a>
        </li>
        <li>
            <a href="https://www.twitter.com/shmuelkamensky"><TwitterIcon></TwitterIcon></a>
        </li>
        <li>
            <a href="mailto:shmuelkamensky@gmail.com"><GmailSvg></GmailSvg></a>
        </li>
        <li>
            <a href="tel:+1917-385-6547"><PhoneUsaSvg></PhoneUsaSvg></a>
        </li>
        <li>
            <a href="tel:+972-53-587-3006"><PhoneILSvg></PhoneILSvg></a>
        </li>

    </ul>
    
  </div>

</div>

<style>
  .contact-container {
    display: flex;
    justify-content: space-between;
    /* align-items: flex-start; */
    padding: 40px;
    
  }

  .contact-details,
  h1{
    color: #333;
  }

  p {
    margin: 10px 0;
    color: #555;
  }


</style>
