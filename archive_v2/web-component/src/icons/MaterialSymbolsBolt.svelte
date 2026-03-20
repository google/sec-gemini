<script lang="ts" module>
  export interface MaterialSymbolsBoltProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = "" }: MaterialSymbolsBoltProps =
    $props();
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{size}em"
  height="{size}em"
  viewBox="0 0 24 24"
  class={className}
>
  <path fill="currentColor" d="m8 22l1-7H4l9-13h2l-1 8h6L10 22z" />
</svg>
