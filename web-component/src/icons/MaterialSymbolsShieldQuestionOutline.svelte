<script lang="ts" module>
  export interface MaterialSymbolsShieldQuestionOutlineProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = '' }: MaterialSymbolsShieldQuestionOutlineProps = $props();
</script>

<svg
   xmlns="http://www.w3.org/2000/svg"
   width="{size}em"
   height="{size}em"
   viewBox="0 0 24 24"
   class="{className}">
  <path fill="currentColor" d="M12 22q-3.475-.875-5.738-3.988T4 11.1V5l8-3l8 3v6.1q0 3.8-2.262 6.913T12 22m0-2.1q2.6-.825 4.3-3.3t1.7-5.5V6.375l-6-2.25l-6 2.25V11.1q0 3.025 1.7 5.5t4.3 3.3m0-2.9q.425 0 .738-.312t.312-.738t-.312-.737T12 14.9t-.737.313t-.313.737t.313.738T12 17m-.725-3.2h1.5v-.55q0-.275.125-.525q.15-.35.4-.587t.525-.488q.425-.425.738-.95t.312-1.15q0-1.125-.862-1.838T12 7q-1 0-1.787.575T9.15 9.1l1.35.55q.15-.5.563-.85T12 8.45q.55 0 .963.325t.412.825q0 .425-.262.788t-.588.662q-.3.275-.6.563t-.475.662q-.175.35-.175.738z"/>
</svg>