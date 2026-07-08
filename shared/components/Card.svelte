<script lang="ts">
  export let title: string = "";
</script>

<div class="card">
  {#if title}
    <h3 class="card-title">{title}</h3>
  {/if}
  <div class="card-content">
    <slot />
  </div>
</div>

<style>
  /* Themeable via --sd-* tokens; defaults are the light app theme. */
  .card {
    background-color: var(--sd-surface, #ffffff);
    color: var(--sd-text, #18181b);
    border: 1px solid var(--sd-border, #e4e4e7);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: var(
      --sd-shadow,
      0 1px 3px rgba(0, 0, 0, 0.05),
      0 10px 15px -3px rgba(0, 0, 0, 0.03),
      0 4px 6px -4px rgba(0, 0, 0, 0.03)
    );
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .card-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--sd-text, #18181b);
    letter-spacing: -0.01em;
    border-bottom: 1px solid var(--sd-border-subtle, #f4f4f5);
    padding-bottom: 0.75rem;
  }

  .card-content {
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--sd-text-muted, #52525b);
  }
</style>
