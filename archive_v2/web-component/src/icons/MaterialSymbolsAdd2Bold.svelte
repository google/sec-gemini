<script lang="ts" module>
  export interface MaterialSymbolsAdd2RoundedProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = "" }: MaterialSymbolsAdd2RoundedProps =
    $props();
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{size}em"
  height="{size}em"
  viewBox="0 0 24 24"
  class={className}
>
  <path
    stroke="currentColor"
    stroke-width="3"
    fill="none"
    d="M12 21q-.425 0-.712-.288T11 20v-7H4q-.425 0-.712-.288T3 12t.288-.712T4 11h7V4q0-.425.288-.712T12 3t.713.288T13 4v7h7q.425 0 .713.288T21 12t-.288.713T20 13h-7v7q0 .425-.288.713T12 21"
  />
</svg>
