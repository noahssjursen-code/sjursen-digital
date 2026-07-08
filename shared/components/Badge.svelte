<script lang="ts">
</script>

<span class="badge">
  <slot />
</span>

<style>
  /* Themeable via --sd-* tokens; defaults are the light app theme. */
  .badge {
    background-color: var(--sd-badge-bg, #f4f4f5);
    color: var(--sd-badge-text, #3f3f46);
    font-weight: 500;
    font-size: 0.75rem;
    letter-spacing: -0.01em;
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    display: inline-block;
    border: 1px solid var(--sd-border, #e4e4e7);
  }
</style>
