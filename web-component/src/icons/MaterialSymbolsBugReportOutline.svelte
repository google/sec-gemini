<script lang="ts" module>
  export interface MaterialSymbolsBugReportOutlineProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = '' }: MaterialSymbolsBugReportOutlineProps = $props();
</script>

<svg
   xmlns="http://www.w3.org/2000/svg"
   width="{size}em"
   height="{size}em"
   viewBox="0 0 24 24"
   class="{className}">
  <path fill="currentColor" d="M12 19q1.65 0 2.825-1.175T16 15v-4q0-1.65-1.175-2.825T12 7T9.175 8.175T8 11v4q0 1.65 1.175 2.825T12 19m-2-3h4v-2h-4zm0-4h4v-2h-4zm2 9q-1.625 0-3.012-.8T6.8 18H4v-2h2.1q-.075-.5-.088-1T6 14H4v-2h2q0-.5.012-1t.088-1H4V8h2.8q.35-.575.788-1.075T8.6 6.05L7 4.4L8.4 3l2.15 2.15q.7-.225 1.425-.225t1.425.225L15.6 3L17 4.4l-1.65 1.65q.575.375 1.038.862T17.2 8H20v2h-2.1q.075.5.088 1T18 12h2v2h-2q0 .5-.013 1t-.087 1H20v2h-2.8q-.8 1.4-2.187 2.2T12 21"/>
</svg>