<script lang="ts" module>
  export interface MaterialSymbolsFilePresentOutlineRoundedProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = '' }: MaterialSymbolsFilePresentOutlineRoundedProps = $props();
</script>

<svg
   xmlns="http://www.w3.org/2000/svg"
   width="{size}em"
   height="{size}em"
   viewBox="0 0 24 24"
   class="{className}">
  <path fill="currentColor" d="M12 19q1.675 0 2.838-1.175T16 15v-3q0-.425-.288-.712T15 11t-.712.288T14 12v3q0 .825-.575 1.413T12 17q-.825 0-1.412-.587T10 15V9.5q0-.225.15-.363T10.5 9q.225 0 .363.138T11 9.5V14q0 .425.288.713T12 15t.713-.288T13 14V9.5q0-1.05-.725-1.775T10.5 7t-1.775.725T8 9.5V15q0 1.65 1.175 2.825T12 19m-6 3q-.825 0-1.412-.587T4 20V4q0-.825.588-1.412T6 2h9l5 5v13q0 .825-.587 1.413T18 22zm0-2h12V8h-3q-.425 0-.712-.288T14 7V4H6zM6 4v4zv16z"/>
</svg>