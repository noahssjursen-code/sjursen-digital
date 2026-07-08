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
    border: 2px solid #000000;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.02em;
    padding: 0.5rem 1.1rem;
    /* Toned-down hand-drawn button profile */
    border-radius: 12px 6px 10px 6px/6px 10px 6px 8px;
    box-shadow: 2px 2px 0px #000000;
    cursor: pointer;
    transition: all 0.1s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .normal-button:hover:not(:disabled) {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px #000000;
  }

  .normal-button:active:not(:disabled) {
    transform: translate(2px, 2px);
    box-shadow: 0px 0px 0px #000000;
  }

  .normal-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #f1f5f9;
  }
</style>
