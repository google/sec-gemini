<script lang="ts" module>
  export interface HugeiconsMenu02Props {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = "" }: HugeiconsMenu02Props = $props();
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{size}em"
  height="{size}em"
  viewBox="0 0 24 24"
  class={className}
>
  <path
    fill="none"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    stroke-width="2"
    d="M4 6h16M4 10h16M4 14h8"
    color="currentColor"
  />
</svg>
