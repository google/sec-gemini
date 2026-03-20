<script>
  import SecGeminiLogo from "../icons/SecGeminiLogo.svelte";

  const { isThinking } = $props();
</script>

<div class="grid w-fit mr-2 place-items-center rounded-lg overflow-visible">
  <div class="relative">
    <SecGeminiLogo
      animate={isThinking}
      size={1.7}
      class={`flex-shrink-0 text-sky-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2`}
    />
  </div>
</div>
