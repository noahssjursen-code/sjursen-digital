<script lang="ts">
  export let type: "button" | "submit" | "reset" = "button";
  export let disabled: boolean = false;
</script>

<button
  {type}
  {disabled}
  class="btn"
  on:click
>
  <slot />
</button>

<style>
  /* Themeable via --sd-* tokens; defaults are the light app theme. */
  .btn {
    background-color: var(--sd-action, #18181b);
    color: var(--sd-action-text, #ffffff);
    border: 1px solid var(--sd-action, #18181b);
    font-weight: 500;
    font-size: 0.875rem;
    letter-spacing: -0.01em;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .btn:hover:not(:disabled) {
    background-color: var(--sd-action-hover, #27272a);
    border-color: var(--sd-action-hover, #27272a);
    transform: translateY(-0.5px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
  }

  .btn:active:not(:disabled) {
    transform: translateY(0.5px);
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
  }

  .btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background-color: var(--sd-disabled, #f4f4f5);
    color: var(--sd-disabled-text, #a1a1aa);
    border-color: var(--sd-border, #e4e4e7);
    box-shadow: none;
  }
</style>
