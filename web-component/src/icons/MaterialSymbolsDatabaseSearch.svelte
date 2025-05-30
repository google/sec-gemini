<script lang="ts" module>
  export interface MaterialSymbolsDatabaseSearchProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = '' }: MaterialSymbolsDatabaseSearchProps = $props();
</script>

<svg
   xmlns="http://www.w3.org/2000/svg"
   width="{size}em"
   height="{size}em"
   viewBox="0 0 24 24"
   class="{className}">
  <path fill="currentColor" d="M11.8 21q-1.05-.025-2.562-.238t-2.9-.687t-2.363-1.237T3 17v-2.5q0 .9.713 1.588t1.787 1.15t2.363.75t2.412.412q.225.725.613 1.388T11.8 21m-1.775-5.125q-1.125-.125-2.363-.413T5.389 14.7t-1.713-1.137T3 12V9.5q0 .95.788 1.65t1.95 1.188t2.525.75t2.487.362q-.3.55-.488 1.163t-.237 1.262M12 11q-3.725 0-6.363-1.175T3 7t2.638-2.825T12 3q3.75 0 6.375 1.175T21 7t-2.625 2.825T12 11m9.6 12l-2.7-2.7q-.55.325-1.15.513T16.5 21q-1.875 0-3.187-1.312T12 16.5t1.313-3.187T16.5 12t3.188 1.313T21 16.5q0 .65-.187 1.25T20.3 18.9l2.7 2.7zm-5.1-4q1.05 0 1.775-.725T19 16.5t-.725-1.775T16.5 14t-1.775.725T14 16.5t.725 1.775T16.5 19"/>
</svg>