<script lang="ts" module>
  export interface MaterialSymbolsMenuProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = "" }: MaterialSymbolsMenuProps =
    $props();
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{size}em"
  height="{size}em"
  viewBox="0 0 24 24"
  class={className}
>
  <path fill="currentColor" d="M3 18v-2h18v2zm0-5v-2h18v2zm0-5V6h18v2z" />
</svg>
