<script lang="ts" module>
  export interface MaterialSymbolsLightbulb2OutlineProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = '' }: MaterialSymbolsLightbulb2OutlineProps = $props();
</script>

<svg
   xmlns="http://www.w3.org/2000/svg"
   width="{size}em"
   height="{size}em"
   viewBox="0 0 24 24"
   class="{className}">
  <path fill="currentColor" d="M10 18q-.825 0-1.412-.587T8 16v-1.25q-1.425-.975-2.212-2.5T5 9q0-2.925 2.038-4.962T12 2t4.963 2.038T19 9q0 1.725-.788 3.238T16 14.75V16q0 .825-.587 1.413T14 18zm0-2h4v-2.3l.85-.6q1.025-.7 1.588-1.787T17 9q0-2.075-1.463-3.537T12 4T8.463 5.463T7 9q0 1.225.563 2.313T9.15 13.1l.85.6zm0 6q-.425 0-.712-.288T9 21v-1h6v1q0 .425-.288.713T14 22zm2-13"/>
</svg>