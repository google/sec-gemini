<script lang="ts">
  import MaterialSymbolsBolt from "../icons/MaterialSymbolsBolt.svelte";
  import MaterialSymbolsBook2Outline from "../icons/MaterialSymbolsBook2Outline.svelte";
  import MaterialSymbolsClose from "../icons/MaterialSymbolsClose.svelte";
  import MaterialSymbolsErrorOutlineRounded from "../icons/MaterialSymbolsErrorOutlineRounded.svelte";
  import SecGemWhite from "../icons/Sparkle.svelte";
  let { showThinking, setShowThinking, thinkingMessages } = $props();
</script>

<div
  class="absolute left-0 top-4 z-50 w-full bg-base h-full overflow-y-auto [scrollbar-color:transparent_transparent] hover:[scrollbar-color:var(--color-accent)_var(--color-base)] grow max-w-6xl px-2 pb-12"
>
  <div
    class="flex flex-col w-full max-w-6xl relative border-neutral-500/80 border rounded-3xl"
  >
    <div
      class="p-4 pb-2 border-b border-neutral-500/80 flex items-center justify-start w-full"
    >
      <MaterialSymbolsBook2Outline class=" inline" size={1.8} />
      <div class="flex items-center w-full gap-2 md:gap-4 mx-2 md:mx-4">
        <h2 class="text-sm md:text-[16px] w-full">Thinking Interface</h2>
        <!-- <div class="h-[0.8lh] w-[1px] bg-text-muted"></div> -->
        <!-- <button
          popovertarget="thinking-model-popover"
          class="hover:bg-accent-light rounded-full w-full hover:cursor-pointer px-3 py-1 text-text-muted text-sm md:text-[16px]"
        >
          Show Thinking
          <MaterialSymbolsChevronRightRounded
            class="rotate-90 inline"
            size={1.4}
          />
        </button> -->
        <button
          type="button"
          class="hover:opacity-90 hover:cursor-pointer hover:bg-accent rounded-full p-2 focus:outline-none -translate-y-1 translate-x-4 ml-auto"
          onclick={() => setShowThinking(!showThinking)}
          aria-label="close"
        >
          <MaterialSymbolsClose size={1.2} class="text-text" />
        </button>
      </div>
    </div>
    <div
      class={`flex flex-col gap-3 overflow-y-hidden px-2 md:px-4 py-6`}
      id="thinking-messages"
    >
      {#if thinkingMessages.length > 0}
        {#each thinkingMessages as message, i (message.id)}
          <div
            class="p-4 pb-0 w-full min-w-32 animate-slidein opacity-0 flex flex-row gap-2 !mb-0"
          >
            <div class="flex flex-col items-center gap-3 w-8 flex-shrink-0">
              {#if message.state === "tool_result" || message.state === "calling_tool"}
                <MaterialSymbolsBolt
                  size={1.8}
                  class="p-2 flex-shrink-0 bg-accent rounded-full aspect-square -mt-1"
                />
              {:else if message.message_type === "error"}
                <MaterialSymbolsErrorOutlineRounded
                  size={1.8}
                  class="p-2 flex-shrink-0 bg-accent rounded-full aspect-square -mt-1 text-red-500"
                />
              {:else}
                <SecGemWhite
                  size={1.8}
                  class="p-2 flex-shrink-0 bg-accent rounded-full aspect-square -mt-1"
                />
              {/if}
            </div>
            <div class="flex flex-col">
              <p
                class={`${message.message_type === "error" ? "text-red-500" : ""} "italic mb-1.5 font-medium"`}
              >
                {message.message_type === "error"
                  ? message.status_message || "Error"
                  : message.title}
              </p>
              <p
                class={`${message.message_type === "error" ? "text-red-500" : ""} "italic text-sm"`}
              >
                {message.content}
              </p>
            </div>
          </div>
        {/each}
      {:else}
        <div class="text-center text-gray-500 py-6">
          No thinking messages yet...
        </div>
      {/if}
    </div>
  </div>
</div>
