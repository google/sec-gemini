<script lang="ts">
  import { MessageTypeEnum } from "sec-gemini";
  import md from "./markdown.ts";
  import MaterialSymbolsThumbUpOutline from "../icons/MaterialSymbolsThumbUpOutline.svelte";
  import MaterialSymbolsThumbDownOutline from "../icons/MaterialSymbolsThumbDownOutline.svelte";
  import MaterialSymbolsShareOutline from "../icons/MaterialSymbolsShareOutline.svelte";
  import FeedbackModal from "./feedback-modal.svelte";
  import BugModal from "./bug-modal.svelte";
  import MaterialSymbolsBugReportOutline from "../icons/MaterialSymbolsBugReportOutline.svelte";
  import MaterialSymbolsContentCopyOutlineRounded from "../icons/MaterialSymbolsContentCopyOutlineRounded.svelte";
  import MaterialSymbolsThumbUp from "../icons/MaterialSymbolsThumbUp.svelte";
  import MaterialSymbolsThumbDown from "../icons/MaterialSymbolsThumbDown.svelte";
  import { onMount } from "svelte";
  import WordAnimation from "./word-animation.svelte";
  import MaterialSymbolsChevronRightRounded from "../icons/MaterialSymbolsChevronRightRounded.svelte";
  import SecGeminiLogoDuel from "../icons/SecGeminiLogoDuel.svelte";

  let feedbackHistory = $state<
    Array<{ messageId: any; type: "like" | "dislike" }>
  >([]);

  let { messages, session, isSessionLogging } = $props();

  const setFeedbackHistory = (
    newFeedbackHistory: {
      messageId: string;
      type: "like" | "dislike";
    }[]
  ) => {
    feedbackHistory = newFeedbackHistory;
  };

  let scrollable: Element | null = $state(null);

  function feedbackExists(id: string | undefined) {
    const feedbackItems = feedbackHistory.filter(
      (item: { messageId: string; type: "like" | "dislike" }) =>
        item.messageId === id
    );

    let isLiked = false;
    let isDisliked = false;

    feedbackItems.forEach((item) => {
      if (item.type === "like") {
        isLiked = true;
      } else if (item.type === "dislike") {
        isDisliked = true;
      }
    });

    return { isLiked, isDisliked };
  }

  onMount(() => {
    if (typeof localStorage === "undefined") {
      console.error("Local storage is not available.");
      // toast.push("Please enable local storage to allow feedback history");
    } else {
      const storedFeedback = localStorage.getItem("feedbackHistory");
      if (storedFeedback) {
        try {
          feedbackHistory = JSON.parse(storedFeedback);
        } catch (error) {
          console.error(
            "Error parsing feedback history from localStorage:",
            error
          );
          feedbackHistory = [];
        }
      }
    }
  });

  function scrollToBottom() {
    if (scrollable) {
      scrollable.scrollTo({
        top: scrollable.scrollHeight,
        left: 0,
        behavior: "smooth",
      });
    }
  }
  const handleLike = (messageId: string | undefined) => {
    const likeDialog = document
      .querySelector("sec-gem-chat")!
      .shadowRoot!.getElementById(
        `like-modal-${messageId}`
      ) as HTMLDialogElement;
    if (likeDialog) {
      likeDialog.showModal();
    }
  };
  const handleDislike = (messageId: string | undefined) => {
    const dislikeDialog = document
      .querySelector("sec-gem-chat")!
      .shadowRoot!.getElementById(
        `dislike-modal-${messageId}`
      ) as HTMLDialogElement;
    if (dislikeDialog) {
      dislikeDialog.showModal();
    }
  };
  const handleBug = (messageId: string | undefined) => {
    console.log(messageId);
    const bugDialog = document
      .querySelector("sec-gem-chat")!
      .shadowRoot!.getElementById(
        `bug-modal-${messageId}`
      ) as HTMLDialogElement;
    if (bugDialog) {
      bugDialog.showModal();
    }
  };

  const handleShare = async (content: string | undefined | null) => {
    if (navigator.share && content) {
      try {
        await navigator.share({ text: content });
      } catch (error) {
        console.error("Error sharing chat:", error);
      }
    } else {
      // toast.push("Web Share API is not supported on this browser.");
    }
  };
  const handleCopy = async (content: string | undefined | null) => {
    if (content) {
      try {
        await navigator.clipboard.writeText(content);
        //   toast.push("Chat copied to clipboard!");
      } catch (err) {
        console.error("Failed to copy text: ", err);
      }
    } else {
      // toast.push("Failed to copy code");
    }
  };

  let queryMessageCount = $derived(
    messages.filter(
      (msg: { message_type: string }) => msg.message_type === "query"
    ).length
  );

  $effect(() => {
    if (queryMessageCount > 1) {
      setTimeout(scrollToBottom, 100);
      const copyButtons = document.querySelectorAll(
        ".copy-code"
      ) as NodeListOf<HTMLButtonElement>;

      copyButtons.forEach((copyButton) => {
        copyButton.addEventListener("click", async () => {
          const rawCode = copyButton.dataset.rawCode;
          if (rawCode) {
            try {
              await navigator.clipboard.writeText(rawCode);
              // toast.push("Code copied to clipboard!");
              setTimeout(() => {
                copyButton.innerHTML = `<svg class="absolute top-1.5 right-1.5 text-inherit" xmlns="http://www.w3.org/2000/svg" width="1.5em" height="1.5em" viewBox="0 0 24 24" {...props}>
                  <path fill="currentColor" d="M15 20H5V7c0-.55-.45-1-1-1s-1 .45-1 1v13c0 1.1.9 2 2 2h10c.55 0 1-.45 1-1s-.45-1-1-1m5-4V4c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h9c1.1 0 2-.9 2-2m-2 0H9V4h9z" />
                  </svg>`;
              }, 1500);
            } catch (err) {
              console.error("Failed to copy text: ", err);
              copyButton.textContent = "Error";
            }
          }
        });
      });
    }
  });

  function toggleHeight(event: Event) {
    const button = event.target as HTMLElement;
    const messageDiv = button.nextElementSibling;
    if (messageDiv) {
      messageDiv.classList.toggle("line-clamp-3");
      messageDiv.classList.toggle("overflow-clip");
    }

    // Toggle the rotation of the button (optional)
    button.classList.toggle("rotate-90");
    button.classList.toggle("-rotate-90");
  }
</script>

<div
  class={`prose min-h-[calc(80vh-(300px))]  max-w-none prose-code:bg-accent prose-code:text-sm prose-code:text-text prose-code:px-2 prose-code:rounded-md prose-p:first:!mt-2 prose-headings:!text-text prose-a:!text-text prose-strong:!text-text !text-text flex-1 overflow-y-auto px-2 md:px-4 py-6 pb-[150px] space-y-4`}
  id="chat-messages"
  bind:this={scrollable}
>
  {#each messages as message, i (message.id)}
    {#if message.role === "user" && message.content}
      <div
        class="bg-accent p-4 rounded-tr-none rounded-3xl w-fit ml-auto min-w-32 max-w-lg animate-slidein opacity-0"
      >
        {#if message.content.length > 170}
          <button
            onclick={toggleHeight}
            class="rounded-full hover:bg-accent-light p-2 hover:cursor-pointer float-right rotate-90"
          >
            <MaterialSymbolsChevronRightRounded
              size={1.4}
              class="pointer-events-none"
            />
          </button>
        {/if}
        <div class="line-clamp-3 overflow-clip">
          {message.content}
        </div>
      </div>
    {:else if message.role === "agent" || message.role === "system"}
      <div class="flex gap-2 chat group">
        <div class="rounded-full flex h-full items-center">
          <SecGeminiLogoDuel
            class="mt-1.5"
            animate={message.message_type === MessageTypeEnum.INFO}
            incognito={!isSessionLogging}
            size={2}
          />
        </div>
        <div
          class="{message.streaming
            ? ''
            : 'animation-finished'} overflow-x-auto {message.message_type ===
          MessageTypeEnum.ERROR
            ? 'bg-accent'
            : ''} {message.message_type === MessageTypeEnum.RESULT ||
          message.message_type === MessageTypeEnum.INFO
            ? 'block min-h-20'
            : 'hidden'} "
        >
          {#if message.streaming}
            <WordAnimation>
              {@html md.render(message.content)}
            </WordAnimation>
          {:else}
            {@html md.render(message.content)}
          {/if}
          <div
            class={`${message.streaming || i === 0 ? "hidden feedback" : "flex"} ${i === messages.length - 1 ? "opacity-100" : "opacity-0 group-hover:opacity-100 transition-opacity duration-400 ease-in-out"} -mt-1.5 pb-4`}
          >
            {#if feedbackExists(message.id).isLiked}
              <button
                class="rounded-full text-blue p-2 hover:cursor-not-allowed"
              >
                <MaterialSymbolsThumbUp size={1.25} />
              </button>
            {:else}
              <button
                onclick={() => handleLike(message.id)}
                class={`rounded-full hover:bg-accent text-text-muted p-2 ${feedbackExists(message.id).isDisliked ? "hover:bg-transparent pointer-events-none" : "hover:cursor-pointer"}`}
              >
                <MaterialSymbolsThumbUpOutline size={1.25} />
              </button>
            {/if}
            {#if feedbackExists(message.id).isDisliked}
              <button
                class="rounded-full text-blue p-2 hover:cursor-not-allowed"
              >
                <MaterialSymbolsThumbDown size={1.25} />
              </button>
            {:else}
              <button
                onclick={() => handleDislike(message.id)}
                class={`rounded-full hover:bg-accent text-text-muted p-2 ${feedbackExists(message.id).isLiked ? "hover:bg-transparent pointer-events-none" : "hover:cursor-pointer"}`}
              >
                <MaterialSymbolsThumbDownOutline size={1.25} />
              </button>
            {/if}
            <button
              onclick={() => handleShare(message.content)}
              class="rounded-full hover:bg-accent p-2 hover:cursor-pointer"
            >
              <MaterialSymbolsShareOutline size={1.25} />
            </button>
            <button
              onclick={() => handleCopy(message.content)}
              class="rounded-full hover:bg-accent p-2 hover:cursor-pointer"
            >
              <MaterialSymbolsContentCopyOutlineRounded size={1.25} />
            </button>
            <button
              onclick={() => handleBug(message.id)}
              class="rounded-full hover:bg-accent p-2 hover:cursor-pointer"
            >
              <MaterialSymbolsBugReportOutline size={1.4} />
            </button>
            <!-- <button
              class="p-2 my-auto text-sm ml-auto mr-2 h-auto w-auto flex sm:min-w-32 items-center justify-center gap-1 rounded-full bg-base border border-text/50 hover:bg-accent disabled:pointer-events-none disabled:hover:bg-transparent hover:cursor-pointer"
              onclick={() => toggleView()}
            >
              <span class="hidden md:inline">Toggle Thinking</span>
              <span class="inline md:hidden">Thinking</span>
            </button> -->
          </div>
        </div>
      </div>
    {:else if message.role === "system"}
      {#if message.content === "working"}
        <div class="flex items-center gap-4">
          <div
            class="skeleton h-10 w-10 shrink-0 rounded-full p9-gradient gradient"
          ></div>
          <div class="flex flex-col gap-1">
            <div class="skeleton h-2 w-48 p9-gradient gradient"></div>
            <div class="skeleton h-2 w-48 p9-gradient gradient"></div>
            <div class="skeleton h-2 w-16 p9-gradient gradient"></div>
          </div>
        </div>
      {/if}
    {/if}
    <FeedbackModal
      id={`like-modal-${message.id}`}
      groupId={message.id}
      feedbackType="like"
      content={message.content}
      {setFeedbackHistory}
      {feedbackHistory}
      {session}
    />
    <FeedbackModal
      id={`dislike-modal-${message.id}`}
      groupId={message.id}
      feedbackType="dislike"
      content={message.content}
      {setFeedbackHistory}
      {feedbackHistory}
      {session}
    />
    <BugModal id={`bug-modal-${message.id}`} groupId={message.id} {session} />
  {/each}
</div>
