<script lang="ts">
  export let title: string = "";
</script>

<div class="normal-card">
  {#if title}
    <h3 class="normal-card-title">{title}</h3>
  {/if}
  <div class="normal-card-content">
    <slot />
  </div>
</div>

<style>
  .normal-card {
    background-color: #ffffff;
    color: #000000;
    border: 3px solid #000000;
    /* This creates the hand-drawn organic wobbly border line look */
    border-radius: 255px 15px 225px 15px/15px 225px 15px 255px;
    padding: 1.5rem;
    box-shadow: 6px 6px 0px #000000;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .normal-card-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: -0.01em;
    border-bottom: 2.5px solid #000000;
    padding-bottom: 0.4rem;
    border-radius: 4px 125px 5px 125px/5px 15px 6px 15px;
  }

  .normal-card-content {
    font-size: 1rem;
    line-height: 1.4;
  }
</style>
