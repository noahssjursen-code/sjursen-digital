<script lang="ts">
  export let type: "button" | "submit" | "reset" = "button";
  export let disabled: boolean = false;
</script>

<button
  {type}
  {disabled}
  class="normal-button"
  on:click
>
  <slot />
</button>

<style>
  .normal-button {
    background-color: #ffffff;
    color: #000000;
    border: 3px solid #000000;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    padding: 0.6rem 1.2rem;
    /* Hand-drawn button profile */
    border-radius: 125px 5px 95px 5px/15px 95px 8px 115px;
    box-shadow: 4px 4px 0px #000000;
    cursor: pointer;
    transition: all 0.1s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .normal-button:hover:not(:disabled) {
    transform: translate(-1px, -1px);
    box-shadow: 5px 5px 0px #000000;
  }

  .normal-button:active:not(:disabled) {
    transform: translate(4px, 4px);
    box-shadow: 0px 0px 0px #000000;
  }

  .normal-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #f1f5f9;
  }
</style>
