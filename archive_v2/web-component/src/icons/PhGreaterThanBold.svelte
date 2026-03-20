<script lang="ts" module>
  export interface PhGreaterThanBoldProps {
    size?: number;
    class?: string;
  }
</script>

<script lang="ts">
  const { size = 0.7, class: className = "" }: PhGreaterThanBoldProps =
    $props();
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  width="{size}em"
  height="{size}em"
  viewBox="0 0 256 256"
  class={className}
>
  <path
    stroke="currentColor"
    stroke-width="32"
    fill="currentColor"
    d="M228 128a12 12 0 0 1-6.86 10.84l-152 72a12 12 0 0 1-10.27-21.69L188 128L58.87 66.85a12 12 0 0 1 10.27-21.69l152 72A12 12 0 0 1 228 128"
  />
</svg>
