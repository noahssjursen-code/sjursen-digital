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
    border: 2px solid #000000;
    /* A more subtle hand-drawn organic curve */
    border-radius: 16px 8px 14px 10px/8px 16px 10px 14px;
    padding: 1.5rem;
    box-shadow: 3px 3px 0px #000000;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .normal-card-title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: -0.01em;
    border-bottom: 2px solid #000000;
    padding-bottom: 0.4rem;
    border-radius: 6px 12px 4px 12px/4px 6px 4px 6px;
  }

  .normal-card-content {
    font-size: 1rem;
    line-height: 1.4;
  }
</style>
