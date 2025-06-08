<svelte:options customElement="sec-gem-chat" />

<script lang="ts">
  import SecGemini, {
    MessageTypeEnum,
    MimeTypeEnum,
    Streamer,
    type Message,
  } from "sec-gemini";
  import { onMount } from "svelte";
  import MaterialSymbolsAdd2Rounded from "../icons/MaterialSymbolsAdd2Rounded.svelte";
  import PhGreaterThanBold from "../icons/PhGreaterThanBold.svelte";
  import SecGeminiLogo from "../icons/SecGeminiLogo.svelte";
  import MessageList from "./message-list.svelte";
  import Thinking from "./thinking.svelte";
  import MaterialSymbolsClose from "../icons/MaterialSymbolsClose.svelte";
  import MdiIncognito from "../icons/MdiIncognito.svelte";

  const {
    resumeSession,
    theme = "light",
    incognito = true,
    sessionDescription,
    sessionName,
  } = $props();

  let compiledGlobStyles = $state("");
  let sanitizedStyleContent = $state("");

  const securityTopics = [
    {
      id: 1,
      title: "Network Security",
      prompt:
        "What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?",
    },
    {
      id: 2,
      title: "Cryptography",
      prompt:
        "Explain the concept of public-key cryptography and provide a real-world example of its application.",
    },
  ];

  interface MessageWithStreaming extends Message {
    streaming?: boolean;
  }

  let apiKey = $state(localStorage.getItem("p9_api_key") || "");
  let inputApiKey = $state(localStorage.getItem("p9_api_key") || "");
  let isKeySet = $derived(!!apiKey);
  let isLoading = $state(false);
  let isLoggingIn = $state(false);
  let errorMessage = $state("");
  let dialog: null | HTMLDialogElement = null;
  let isChatExpanded = $state(false);
  let scrollable: null | HTMLDivElement = $state(null);
  let isProcessing: boolean = $state(false);
  let messageInput: null | HTMLTextAreaElement = $state(null);
  let isSessionLogging: boolean = $state(true);
  let showThinking: boolean = $state(false);

  let secGemSDK: SecGemini;
  let session: any = $state(null);
  let currentStreamer: Streamer | null = $state(null);
  let messages: MessageWithStreaming[] = $state([]);
  let thinkingMessages: MessageWithStreaming[] = $state([]);
  let input_field = $state("");

  $effect(() => {
    isProcessing = messages.some(
      (msg) =>
        (msg.role === "agent" && msg.message_type === MessageTypeEnum.INFO) ||
        (msg.role === "system" && msg.content === "working")
    );
  });

  function setPrompt(prompt: string) {
    input_field = prompt;
  }

  async function handleFileUpload() {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.multiple = false;
    fileInput.accept = Object.values(MimeTypeEnum).join(",");
    fileInput.onchange = async (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        const fileContent = await readFileAsArrayBuffer(file);
        await session.attachFile(file.name, "mimeType", fileContent);
      } catch (error) {
        console.error("Error attaching file:", error);
      }
    };
    fileInput.click();
  }
  function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (reader.result instanceof ArrayBuffer) {
          resolve(reader.result);
        } else {
          reject(new Error("Failed to read file as ArrayBuffer"));
        }
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  }

  function scrollToTop() {
    if (scrollable) {
      scrollable.scrollTo({
        top: scrollable.scrollHeight - 450,
        left: 0,
        behavior: "smooth",
      });
    }
  }

  function onmessage(message: Message) {
    let now = Date.now();
    if (message.message_type === "thinking") {
      thinkingMessages.push(message);
    }
    switch (message.message_type) {
      case MessageTypeEnum.RESULT:
        messages = [...messages, { ...message, streaming: true }].filter(
          (msg) => msg.role !== "system"
        );
        break;
      case MessageTypeEnum.INFO:
        if (
          messages.length > 0 &&
          messages[messages.length - 1].role === "system"
        ) {
          messages = messages.slice(0, -1);
        }
        messages = [...messages, message];
        break;
      case MessageTypeEnum.ERROR:
        messages = [...messages, message].filter(
          (msg) => msg.role !== "system"
        );
        errorMessage = message.content ?? "";
        break;
      default:
        console.debug("Received message type", message.message_type);
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      if (input_field) {
        const trimmedPrompt = input_field.trim();
        if (trimmedPrompt && !isProcessing) {
          handleSend(event);
        }
      }
    }
  }

  function handleSend(e: Event) {
    e.preventDefault();
    if (input_field.trim().length >= 3) {
      const userMessage: Message = {
        id: crypto.randomUUID(),
        timestamp: Date.now() / 1000,
        message_type: "query",
        role: "user",
        content: input_field,
        mime_type: "text/plain",
      };
      const placeHolderMessage: MessageWithStreaming = {
        id: crypto.randomUUID(),
        timestamp: Date.now() / 1000,
        message_type: "info",
        role: "system",
        content: "Just a sec...",
        mime_type: "text/plain",
        streaming: true,
      };

      messages = [...messages, userMessage, placeHolderMessage];

      setTimeout(scrollToTop, 100);

      currentStreamer!.send(input_field);
      input_field = "";
    }
  }

  async function saveApiKey() {
    if (!inputApiKey.trim()) {
      errorMessage = "Please enter a valid API key";
      return;
    }

    isLoggingIn = true;
    errorMessage = "";

    try {
      const testP9 = await SecGemini.create(inputApiKey);
      if (!testP9) {
        throw new Error("Failed to initialize SDK with the provided API key");
      }

      localStorage.setItem("p9_api_key", inputApiKey);
      apiKey = inputApiKey;
      isKeySet = true;
      if (dialog) {
        dialog.showModal();
        isChatExpanded = true;
      }

      initializeSDK();
    } catch (error) {
      console.error("API Key validation failed:", error);
      errorMessage = "Invalid API key. Please check and try again.";
    } finally {
      isLoggingIn = false;
    }
  }

  function clearApiKey() {
    localStorage.removeItem("p9_api_key");
    apiKey = "";
    isKeySet = false;
    messages = [
      {
        id: "initial-assistant-id",
        timestamp: Date.now() / 1000,
        message_type: "result",
        role: "agent",
        content: "How can I help you today?",
        mime_type: "text/plain",
      },
    ];
  }

  async function initializeSDK() {
    try {
      isLoading = true;
      secGemSDK = await SecGemini.create(apiKey);
      if (resumeSession) {
        session = await secGemSDK.resumeSession(resumeSession);
        isSessionLogging = session._session.can_log;
        // logging = session.
        session._session.messages.length > 0 &&
          (messages = session._session.messages.filter(
            (message: { message_type: string }) =>
              message.message_type === "result" ||
              message.message_type === "query"
          ));
      } else {
        session = await secGemSDK.createSession({
          name: sessionName,
          description: sessionDescription,
          logSession: Boolean(!incognito),
          model: "stable",
          language: "en-US",
        });
        isSessionLogging = session._session.can_log;
      }
      console.log("incognito", !isSessionLogging);
      currentStreamer = await session.streamer(onmessage as any);
      isLoading = false;
    } catch (error) {
      console.error("Failed to initialize SDK:", error);
      errorMessage =
        "Failed to initialize chat. Please check your API key and try again.";
      isLoading = false;
      isKeySet = false;
    }
  }

  function toggleChat() {
    isChatExpanded = !isChatExpanded;
    if (scrollable) {
      const elementsToRemoveAnimation =
        scrollable.querySelectorAll(".animate-slidein");
      elementsToRemoveAnimation.forEach((el) => {
        el.classList.remove("animate-slidein");
        el.classList.remove("opacity-0");
      });
    }
    messages = messages.map((msg) => ({ ...msg, streaming: false }));
    if (isChatExpanded) {
      dialog!.showModal();
    } else {
      dialog!.close();
    }

    if (isChatExpanded && isKeySet) {
      setTimeout(() => {
        const messagesContainer = document.querySelector(".messages-container");
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      }, 100);
    }
  }

  function handleClickOutside(event: Event) {
    if (dialog && event.target === dialog) {
      dialog.close();
      isChatExpanded = false;
    }
  }

  function resizeTextarea() {
    if (!messageInput) return;
    messageInput.style.height = "auto";
    const newHeight = Math.min(messageInput.scrollHeight, 200);
    messageInput.style.height = `${newHeight}px`;
  }

  onMount(async () => {
    if (apiKey) {
      initializeSDK();
    }
    const fontFaces = `@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&family=Noto+Sans+Mono:wght@100..900&family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap');`;
    const style = document.createElement("style");
    style.textContent = fontFaces;
    document.head.appendChild(style);
  });
</script>

<div id="wrapper" class="font-base" data-theme={theme}>
  <button
    aria-label="toggle"
    class={`${isChatExpanded ? "border-blue" : "border-transparent"} fixed bottom-5 right-5 w-50 h-15 rounded-3xl bg-base border-4 font-base text-text text-sm cursor-pointer flex items-center justify-center z-10 transition-all duration-300 ease-in-out p-0 shadow-md`}
    onclick={toggleChat}
  >
    Ask Sec-Gemini
    <SecGeminiLogo class="inline h-5 w-5 flex-shrink-0 mb-1 ml-2" />
  </button>
  <dialog
    onmousedown={handleClickOutside}
    bind:this={dialog}
    class="chatbot-container fixed inset-0 left-1/2 top-20 z-50 w-screen max-w-3xl h-[80vh] -translate-x-1/2 translate-y-0 opacity-0 transform bg-base p-2 rounded-3xl text-text backdrop:backdrop-blur-xs backdrop:bg-base/50 backdrop-blur-lg transition-[overlay,display,opacity] duration-300 transition-discrete backdrop:transition-[overlay,display,opacity] backdrop:duration-300 backdrop:transition-discrete open:block open:opacity-100 open:starting:opacity-0 overflow-clip"
  >
    <div class="flex flex-col h-full w-full p-4 pb-1 bg-base">
      <div class="flex justify-between items-center py-2">
        <h2
          class="text-center text-text text-xl md:text-2xl font-bold inline-block"
        >
          Sec-Gemini
        </h2>
        {#if isKeySet}
          <div class="flex gap-2">
            <button
              class="p-2 my-auto text-sm ml-auto mr-2 h-auto w-auto flex sm:min-w-32 items-center justify-center gap-1 rounded-full bg-base border border-text/50 hover:bg-accent disabled:pointer-events-none disabled:hover:bg-transparent hover:cursor-pointer"
              onclick={() => (showThinking = !showThinking)}
            >
              <span class="hidden md:inline">Toggle Thinking</span>
              <span class="inline md:hidden">Thinking</span>
            </button>
            <button
              class="bg-transparent border-none cursor-pointer p-2 flex items-center justify-center hover:bg-accent rounded-full"
              onclick={toggleChat}
              aria-label="ToggleChat"
            >
              <MaterialSymbolsClose size={1.7} />
            </button>
          </div>
        {/if}
      </div>
      {#if !isKeySet}
        <div class="p-4 flex flex-col justify-center items-center h-full">
          <p class="mb-4 text-text">
            Please enter your API key to access the chat interface.
          </p>
          <div class="flex rounded-md shadow-sm w-full max-w-md">
            <input
              type="password"
              placeholder="Enter your API key"
              bind:value={inputApiKey}
              onkeydown={(e) => e.key === "Enter" && saveApiKey()}
              class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-l-md border border-gray-300 focus:ring-blue focus:border-blue focus:z-10 sm:text-sm"
            />
            <button
              onclick={saveApiKey}
              disabled={isLoggingIn}
              class={`${isLoggingIn ? "animate-pulse" : ""} btn relative inline-flex items-center px-4 min-w-10 py-2 rounded-l-none isabled:bg-accent disabled:cursor-not-allowed disabled:text-text-muted bg-blue text-white`}
            >
              {isLoggingIn ? "..." : "Go"}
            </button>
          </div>
          {#if errorMessage}
            <div
              class="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md text-sm"
            >
              {errorMessage}
            </div>
          {/if}
        </div>
      {:else}
        {#if showThinking}
          <Thinking
            setShowThinking={() => (showThinking = !showThinking)}
            {showThinking}
            thinkingMessages={thinkingMessages.filter(
              (msg) => msg.message_type === "thinking"
            )}
          />
        {/if}
        {#if messages.length === 0}
          <div class="-mb-10">
            <p
              class="text-start bg-[linear-gradient(90deg,#217BFE_0%,#078EFB_33%,#AC87EB_67%,#EE4D5D_100%)] text-transparent tracking-wide w-fit bg-clip-text py-2 text-lg md:text-xl font-semibold inline-block"
            >
              Hello
            </p>
            <br />
            <p
              class="text-start text-text-muted md:text-lg font-medium py-2 inline-block"
            >
              How can I help you?
            </p>
            <div class="flex flex-col gap-1 justify-center">
              <p
                class="text-start text-text-muted md:text-lg font-medium py-2 inline-block"
              >
                Examples
              </p>
              {#each securityTopics as topic, index (topic.id)}
                <button
                  onclick={() => setPrompt(topic.prompt)}
                  class={`w-full animate-background hover:bg-[linear-gradient(152deg,_#217BFE,_#078EFB_42%,_#AC87EB)] bg-[length:_400%_400%] p-[1px] transition-colors ease-in-out duration-1000 [animation-duration:_6s] relative hover:cursor-pointer rounded-xl text-start flex flex-col gap-2`}
                >
                  <div
                    class="bg-accent-dark rounded-xl h-full w-full py-3 px-2"
                  >
                    <p class="text-text text-sm mb-1 line-clamp-1">
                      {topic.title}
                    </p>
                    <p class="text-text-muted text-sm line-clamp-4">
                      {topic.prompt}
                    </p>
                  </div>
                </button>
              {/each}
            </div>
          </div>
        {:else}
          <MessageList {messages} {session} {isSessionLogging} />
        {/if}
        <form class="flex items-end gap-2 mt-auto" onsubmit={handleSend}>
          <div
            class={`flex-1 border ${isSessionLogging ? "border-neutral-500/80" : "border-purple"} bg-base rounded-3xl overflow-hidden`}
          >
            <textarea
              bind:this={messageInput}
              bind:value={input_field}
              oninput={resizeTextarea}
              onkeydown={handleKeyDown}
              class="w-full px-4 py-3 resize-none focus:outline-none min-h-[56px] max-h-[130px] placeholder:text-text-muted"
              placeholder={isProcessing
                ? "Waiting for response..."
                : "Ask Sec-Gemini"}
              rows="1"
              disabled={isProcessing}
            ></textarea>
            <div class="p-2 pb-0 flex justify-between">
              <div class="flex gap-2 items-center">
                <button
                  onclick={handleFileUpload}
                  aria-label="add"
                  type="button"
                  class="p-3 rounded-full bg-accent-light text-text disabled:opacity-20 disabled:cursor-not-allowed hover:cursor-pointer flex items-center justify-center"
                  disabled={isProcessing}
                >
                  <MaterialSymbolsAdd2Rounded
                    size={1}
                    class="flex-shrink-0 text-text"
                  />
                </button>
              </div>
              <div class="p-2 flex gap-2 justify-between">
                {#if !isSessionLogging}
                  <div
                    class={"w-full p-1 sm:p-3 rounded-3xl text-purple text-sm flex items-center justify-start gap-2 font-medium"}
                  >
                    <MdiIncognito size={1.7} />
                  </div>
                {/if}
                <button
                  aria-label="submit"
                  type="submit"
                  class={`${input_field.length === 0 || isProcessing ? "hidden" : "flex"} p-2 h-8 w-8 my-auto sm:h-auto sm:w-auto text-base disabled:text-accent sm:min-w-32 items-center justify-center gap-1 rounded-full bg-text hover:bg-text-muted disabled:hover:bg-text disabled:opacity-50 dark:disabled:opacity-50 disabled:cursor-not-allowed hover:cursor-pointer`}
                  disabled={input_field.length === 0 || isProcessing}
                >
                  <span
                    class={`${isProcessing ? "bg-[linear-gradient(90deg,#217BFE_0%,#078EFB_33%,#AC87EB_67%,#EE4D5D_100%)] text-transparent bg-clip-text animate-gradient bg-[length:200%_auto]" : ""} hidden sm:inline-block`}
                    >{isProcessing ? "Thinking" : "Send"}</span
                  >
                  <div class="sm:hidden">
                    <PhGreaterThanBold
                      size={1}
                      class={`${isProcessing ? "bg-[linear-gradient(90deg,#217BFE_0%,#078EFB_33%,#AC87EB_67%,#EE4D5D_100%)] text-transparent bg-clip-text animate-gradient bg-[length:200%_auto]" : ""} flex-shrink-0 text-base`}
                    />
                  </div>
                  {#if !isProcessing}
                    <kbd
                      class="hidden sm:block px-1 py-0.5 text-[12px] font-mono text-gray-800 rounded-md dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
                      ><svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="1em"
                        height="1em"
                        viewBox="0 0 56 56"
                        ><path
                          fill="currentColor"
                          d="M18.93 22.539v10.945h-4.711c-4.594 0-8.367 3.633-8.367 8.274s3.773 8.39 8.367 8.39c4.617 0 8.367-3.75 8.367-8.39V37.07h10.805v4.688c0 4.64 3.773 8.39 8.39 8.39c4.594 0 8.367-3.75 8.367-8.39s-3.773-8.274-8.367-8.274h-4.734V22.54h4.734c4.594 0 8.367-3.633 8.367-8.273c0-4.641-3.773-8.414-8.367-8.414c-4.617 0-8.39 3.773-8.39 8.414v4.687H22.586v-4.687c0-4.641-3.75-8.414-8.367-8.414c-4.594 0-8.367 3.773-8.367 8.414c0 4.64 3.773 8.273 8.367 8.273ZM14.219 19c-2.555 0-4.711-2.133-4.711-4.734s2.156-4.758 4.71-4.758c2.579 0 4.712 2.156 4.712 4.758V19Zm27.562 0h-4.734v-4.734c0-2.602 2.156-4.758 4.734-4.758c2.555 0 4.711 2.156 4.711 4.758S44.336 19 41.782 19M22.586 33.531V22.492h10.805v11.04ZM14.219 37h4.71v4.734c0 2.602-2.132 4.735-4.71 4.735c-2.555 0-4.711-2.133-4.711-4.735c0-2.601 2.156-4.734 4.71-4.734m27.562 0c2.555 0 4.711 2.133 4.711 4.734s-2.156 4.735-4.71 4.735c-2.579 0-4.735-2.133-4.735-4.735V37Z"
                        /></svg
                      ></kbd
                    >
                    <span class="hidden sm:block">+</span>
                    <kbd
                      class="hidden sm:block px-1 py-0.5 text-[12px] font-mono text-gray-800 bg-gray-100 border border-gray-200 rounded-md dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500"
                      ><svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="1em"
                        height="1em"
                        viewBox="0 0 56 56"
                        ><path
                          fill="currentColor"
                          d="M19.281 49.516c1.242 0 2.063-.844 2.063-2.063c0-.61-.188-1.055-.563-1.43l-6.75-6.586l-4.453-3.796l5.508.234h29.906c5.46 0 7.735-2.508 7.735-7.805V14.22c0-5.461-2.274-7.735-7.735-7.735H31.867c-1.289 0-2.133.938-2.133 2.086c0 1.149.844 2.086 2.133 2.086h13.125c2.484 0 3.563 1.078 3.563 3.563v13.85c0 2.555-1.079 3.633-3.563 3.633H15.086l-5.508.235l4.453-3.797l6.75-6.586c.375-.375.563-.844.563-1.453c0-1.196-.82-2.063-2.063-2.063c-.515 0-1.125.258-1.523.656L3.976 32.22c-.468.445-.703.984-.703 1.57c0 .563.235 1.125.703 1.57l13.782 13.524a2.27 2.27 0 0 0 1.523.633"
                        /></svg
                      ></kbd
                    >
                  {/if}
                </button>
              </div>
            </div>
          </div>
        </form>
        <p
          class="text-center text-xs px-2 pb-0 pt-2 line-clamp-1 text-text-muted"
        >
          Prompts and responses will be used to improve Sec-Gemini. It can make
          mistakes, so please double check everything. v0.5
        </p>
        {#if errorMessage}
          <div class="p-3 bg-red-100 text-red-700 rounded-md mt-2">
            {errorMessage}
          </div>
        {/if}
      {/if}
    </div>
  </dialog>
</div>

<style global>
  :global(:host) {
    color: var(--color-text);
  }
  :global(#wrapper[data-theme="dark"]) {
    /* These global styles will now apply when the parent dialog has data-theme="dark" */
    --color-base: #1b1c1d;
    --color-accent: #282a2c;
    --color-accent-light: #32373d;
    --color-accent-dark: #1e1f20;
    --color-accent-blue: #1f3760;
    --color-text-muted: #a2a9b0;
    --color-text: white;
    --color-text-blue: #4285f4;
    --color-highlight: #1f3760;
    --color-yellow: #ffb900;
    --color-blue: #217bfe;
    --color-purple: #ab67e0;
  }
  :global {
    code[class*="language-"],
    pre[class*="language-"] {
      color: #ccc;
      background: none;
      font-family:
        Consolas,
        Monaco,
        Andale Mono,
        Ubuntu Mono,
        monospace;
      font-size: 1em;
      text-align: left;
      white-space: pre;
      word-spacing: normal;
      word-break: normal;
      word-wrap: normal;
      line-height: 1.5;
      -moz-tab-size: 4;
      -o-tab-size: 4;
      tab-size: 4;
      -webkit-hyphens: none;
      -moz-hyphens: none;
      -ms-hyphens: none;
      hyphens: none;
    }

    pre[class*="language-"] {
      padding: 1em;
      margin: 0.5em 0;
      overflow: auto;
    }

    :not(pre) > code[class*="language-"],
    pre[class*="language-"] {
      background: #2d2d2d;
    }

    :not(pre) > code[class*="language-"] {
      padding: 0.1em;
      border-radius: 0.3em;
      white-space: normal;
    }

    .token.comment,
    .token.block-comment,
    .token.prolog,
    .token.doctype,
    .token.cdata {
      color: #999;
    }

    .token.punctuation {
      color: #ccc;
    }

    .token.tag,
    .token.attr-name,
    .token.namespace,
    .token.deleted {
      color: #e2777a;
    }

    .token.function-name {
      color: #6196cc;
    }

    .token.boolean,
    .token.number,
    .token.function {
      color: #f08d49;
    }

    .token.property,
    .token.class-name,
    .token.constant,
    .token.symbol {
      color: #f8c555;
    }

    .token.selector,
    .token.important,
    .token.atrule,
    .token.keyword,
    .token.builtin {
      color: #cc99cd;
    }

    .token.string,
    .token.char,
    .token.attr-value,
    .token.regex,
    .token.variable {
      color: #7ec699;
    }

    .token.operator,
    .token.entity,
    .token.url {
      color: #67cdcc;
    }

    .token.important,
    .token.bold {
      font-weight: 700;
    }

    .token.italic {
      font-style: italic;
    }

    .token.entity {
      cursor: help;
    }

    .token.inserted {
      color: green;
    }

    /*! tailwindcss v4.1.6 | MIT License | https://tailwindcss.com */
    @layer properties;
    @layer theme, base, components, utilities;

    @layer theme {
      :root,
      :host {
        --font-sans: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji",
          "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
        --font-mono: Noto Sans Mono, monospace;
        --color-red-100: oklch(93.6% 0.032 17.717);
        --color-red-700: oklch(50.5% 0.213 27.518);
        --color-sky-500: oklch(68.5% 0.169 237.323);
        --color-gray-100: oklch(96.7% 0.003 264.542);
        --color-gray-200: oklch(92.8% 0.006 264.531);
        --color-gray-300: oklch(87.2% 0.01 258.338);
        --color-gray-500: oklch(55.1% 0.027 264.364);
        --color-gray-600: oklch(44.6% 0.03 256.802);
        --color-gray-800: oklch(27.8% 0.033 256.848);
        --color-neutral-500: oklch(55.6% 0 0);
        --color-black: #000;
        --color-white: #fff;
        --spacing: 0.25rem;
        --container-md: 28rem;
        --container-lg: 32rem;
        --container-3xl: 48rem;
        --text-xs: 0.75rem;
        --text-xs--line-height: calc(1 / 0.75);
        --text-sm: 0.875rem;
        --text-sm--line-height: calc(1.25 / 0.875);
        --text-lg: 1.125rem;
        --text-lg--line-height: calc(1.75 / 1.125);
        --text-xl: 1.25rem;
        --text-xl--line-height: calc(1.75 / 1.25);
        --text-2xl: 1.5rem;
        --text-2xl--line-height: calc(2 / 1.5);
        --font-weight-medium: 500;
        --font-weight-semibold: 600;
        --font-weight-bold: 700;
        --tracking-wide: 0.025em;
        --radius-md: 0.375rem;
        --radius-lg: 0.5rem;
        --radius-xl: 0.75rem;
        --radius-3xl: 1.5rem;
        --ease-out: cubic-bezier(0, 0, 0.2, 1);
        --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
        --animate-pulse: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        --blur-xs: 4px;
        --blur-lg: 16px;
        --default-transition-duration: 150ms;
        --default-transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
        --default-font-family: var(--font-sans);
        --default-mono-font-family: var(--font-mono);
        --tw-border-style: 1px;
        --font-base: Noto Sans, Helvetica Neue, sans-serif;
        --color-base: #f9fafb;
        --color-accent: #f0f4f9;
        --color-accent-light: #575b5f14;
        --color-accent-dark: #d1d5db;
        --color-accent-blue: #dbeafe;
        --color-text-muted: #6b7280;
        --color-text: #1b1c1d;
        --color-text-blue: #0842a0;
        --color-highlight: #d3e3fd;
        --color-yellow: #7b3306;
        --color-blue: #217bfe;
        --color-purple: #8028c3;
        --animate-background: background-move ease infinite;
        --animate-slidein: slidein 1s ease 300ms forwards;
        --animate-gradient: animatedgradient 6s ease infinite alternate;
        --animate-draw-shield: draw-shield 4s ease-in-out infinite;
        --animate-sparkle-sequence: sparkle-sequence 4s ease-in-out infinite;
      }
    }

    @layer base {
      *,
      ::after,
      ::before,
      ::backdrop,
      ::file-selector-button {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        border: 0 solid;
      }

      html,
      :host {
        line-height: 1.5;
        -webkit-text-size-adjust: 100%;
        tab-size: 4;
        font-family: var(
          --default-font-family,
          ui-sans-serif,
          system-ui,
          sans-serif,
          "Apple Color Emoji",
          "Segoe UI Emoji",
          "Segoe UI Symbol",
          "Noto Color Emoji"
        );
        font-feature-settings: var(--default-font-feature-settings, normal);
        font-variation-settings: var(--default-font-variation-settings, normal);
        -webkit-tap-highlight-color: transparent;
      }

      hr {
        height: 0;
        color: inherit;
        border-top-width: 1px;
      }

      abbr:where([title]) {
        -webkit-text-decoration: underline dotted;
        text-decoration: underline dotted;
      }

      h1,
      h2,
      h3,
      h4,
      h5,
      h6 {
        font-size: inherit;
        font-weight: inherit;
      }

      a {
        color: inherit;
        -webkit-text-decoration: inherit;
        text-decoration: inherit;
      }

      b,
      strong {
        font-weight: bolder;
      }

      code,
      kbd,
      samp,
      pre {
        font-family: var(
          --default-mono-font-family,
          ui-monospace,
          SFMono-Regular,
          Menlo,
          Monaco,
          Consolas,
          "Liberation Mono",
          "Courier New",
          monospace
        );
        font-feature-settings: var(
          --default-mono-font-feature-settings,
          normal
        );
        font-variation-settings: var(
          --default-mono-font-variation-settings,
          normal
        );
        font-size: 1em;
      }

      small {
        font-size: 80%;
      }

      sub,
      sup {
        font-size: 75%;
        line-height: 0;
        position: relative;
        vertical-align: baseline;
      }

      sub {
        bottom: -0.25em;
      }

      sup {
        top: -0.5em;
      }

      table {
        text-indent: 0;
        border-color: inherit;
        border-collapse: collapse;
      }

      :-moz-focusring {
        outline: auto;
      }

      progress {
        vertical-align: baseline;
      }

      summary {
        display: list-item;
      }

      ol,
      ul,
      menu {
        list-style: none;
      }

      img,
      svg,
      video,
      canvas,
      audio,
      iframe,
      embed,
      img,
      video {
        max-width: 100%;
        height: auto;
      }

      button,
      input,
      select,
      optgroup,
      textarea,
      ::file-selector-button {
        font: inherit;
        font-feature-settings: inherit;
        font-variation-settings: inherit;
        letter-spacing: inherit;
        color: inherit;
        border-radius: 0;
        background-color: transparent;
        opacity: 1;
      }

      :where(select:is([multiple], [size])) optgroup {
        font-weight: bolder;
      }

      :where(select:is([multiple], [size])) optgroup option {
        padding-inline-start: 20px;
      }

      ::file-selector-button {
        margin-inline-end: 4px;
      }

      ::placeholder {
        opacity: 1;
      }

      @supports (not (-webkit-appearance: -apple-pay-button)) or
        (contain-intrinsic-size: 1px) {
        ::placeholder {
          color: currentcolor;

          @supports (color: color-mix(in lab, red, red)) {
            color: color-mix(in oklab, currentcolor 50%, transparent);
          }
        }
      }

      textarea {
        resize: vertical;
      }

      ::-webkit-search-decoration {
        -webkit-appearance: none;
      }

      ::-webkit-date-and-time-value {
        min-height: 1lh;
        text-align: inherit;
      }

      ::-webkit-datetime-edit {
        display: inline-flex;
      }

      ::-webkit-datetime-edit-fields-wrapper {
        padding: 0;
      }

      ::-webkit-datetime-edit,
      ::-webkit-datetime-edit-year-field,
      ::-webkit-datetime-edit-month-field,
      ::-webkit-datetime-edit-day-field,
      ::-webkit-datetime-edit-hour-field,
      ::-webkit-datetime-edit-minute-field,
      ::-webkit-datetime-edit-second-field,
      ::-webkit-datetime-edit-millisecond-field,
      ::-webkit-datetime-edit-meridiem-field {
        padding-block: 0;
      }

      :-moz-ui-invalid {
        box-shadow: none;
      }

      button,
      input:where([type="button"], [type="reset"], [type="submit"]),
      ::file-selector-button {
        appearance: button;
      }

      ::-webkit-inner-spin-button,
      ::-webkit-outer-spin-button {
        height: auto;
      }

      [hidden]:where(:not([hidden="until-found"])) {
        display: none !important;
      }
    }

    @layer utilities {
      .pointer-events-none {
        pointer-events: none;
      }

      .absolute {
        position: absolute;
      }

      .fixed {
        position: fixed;
      }

      .relative {
        position: relative;
      }

      .inset-0 {
        inset: calc(var(--spacing) * 0);
      }

      .top-1\.5 {
        top: calc(var(--spacing) * 1.5);
      }

      .top-1\/2 {
        top: calc(1 / 2 * 100%);
      }

      .top-1\/4 {
        top: calc(1 / 4 * 100%);
      }

      .top-4 {
        top: calc(var(--spacing) * 4);
      }

      .top-20 {
        top: calc(var(--spacing) * 20);
      }

      .right-1\.5 {
        right: calc(var(--spacing) * 1.5);
      }

      .right-5 {
        right: calc(var(--spacing) * 5);
      }

      .bottom-5 {
        bottom: calc(var(--spacing) * 5);
      }

      .left-0 {
        left: calc(var(--spacing) * 0);
      }

      .left-1\/2 {
        left: calc(1 / 2 * 100%);
      }

      .z-10 {
        z-index: 10;
      }

      .z-50 {
        z-index: 50;
      }

      .float-right {
        float: right;
      }

      .container {
        width: 100%;

        @media (width >=990px) {
          max-width: 990px;
        }

        @media (width >=40rem) {
          max-width: 40rem;
        }

        @media (width >=64rem) {
          max-width: 64rem;
        }

        @media (width >=80rem) {
          max-width: 80rem;
        }

        @media (width >=96rem) {
          max-width: 96rem;
        }
      }

      .mx-2 {
        margin-inline: calc(var(--spacing) * 2);
      }

      .my-auto {
        margin-block: auto;
      }

      .prose {
        color: var(--tw-prose-body);
        max-width: 65ch;

        :where(p):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          margin-top: 1.25em;
          margin-bottom: 1.25em;
        }

        :where([class~="lead"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: var(--tw-prose-lead);
          font-size: 1.25em;
          line-height: 1.6;
          margin-top: 1.2em;
          margin-bottom: 1.2em;
        }

        :where(a):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-links);
          text-decoration: underline;
          font-weight: 500;
        }

        :where(strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: var(--tw-prose-bold);
          font-weight: 600;
        }

        :where(a strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(blockquote strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(thead th strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(ol):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          list-style-type: decimal;
          margin-top: 1.25em;
          margin-bottom: 1.25em;
          padding-inline-start: 1.625em;
        }

        :where(ol[type="A"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: upper-alpha;
        }

        :where(ol[type="a"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: lower-alpha;
        }

        :where(ol[type="A" s]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: upper-alpha;
        }

        :where(ol[type="a" s]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: lower-alpha;
        }

        :where(ol[type="I"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: upper-roman;
        }

        :where(ol[type="i"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: lower-roman;
        }

        :where(ol[type="I" s]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: upper-roman;
        }

        :where(ol[type="i" s]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: lower-roman;
        }

        :where(ol[type="1"]):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          list-style-type: decimal;
        }

        :where(ul):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          list-style-type: disc;
          margin-top: 1.25em;
          margin-bottom: 1.25em;
          padding-inline-start: 1.625em;
        }

        :where(ol > li):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::marker {
          font-weight: 400;
          color: var(--tw-prose-counters);
        }

        :where(ul > li):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::marker {
          color: var(--tw-prose-bullets);
        }

        :where(dt):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-headings);
          font-weight: 600;
          margin-top: 1.25em;
        }

        :where(hr):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          border-color: var(--tw-prose-hr);
          border-top-width: 1;
          margin-top: 3em;
          margin-bottom: 3em;
        }

        :where(blockquote):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          font-weight: 500;
          font-style: italic;
          color: var(--tw-prose-quotes);
          border-inline-start-width: 0.25rem;
          border-inline-start-color: var(--tw-prose-quote-borders);
          quotes: "\201C" "\201D" "\2018" "\2019";
          margin-top: 1.6em;
          margin-bottom: 1.6em;
          padding-inline-start: 1em;
        }

        :where(blockquote p:first-of-type):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::before {
          content: open-quote;
        }

        :where(blockquote p:last-of-type):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::after {
          content: close-quote;
        }

        :where(h1):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-headings);
          font-weight: 800;
          font-size: 2.25em;
          margin-top: 0;
          margin-bottom: 0.8888889em;
          line-height: 1.1111111;
        }

        :where(h1 strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          font-weight: 900;
          color: inherit;
        }

        :where(h2):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-headings);
          font-weight: 700;
          font-size: 1.5em;
          margin-top: 2em;
          margin-bottom: 1em;
          line-height: 1.3333333;
        }

        :where(h2 strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          font-weight: 800;
          color: inherit;
        }

        :where(h3):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-headings);
          font-weight: 600;
          font-size: 1.25em;
          margin-top: 1.6em;
          margin-bottom: 0.6em;
          line-height: 1.6;
        }

        :where(h3 strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          font-weight: 700;
          color: inherit;
        }

        :where(h4):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-headings);
          font-weight: 600;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          line-height: 1.5;
        }

        :where(h4 strong):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          font-weight: 700;
          color: inherit;
        }

        :where(img):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          margin-top: 2em;
          margin-bottom: 2em;
        }

        :where(picture):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          display: block;
          margin-top: 2em;
          margin-bottom: 2em;
        }

        :where(video):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 2em;
          margin-bottom: 2em;
        }

        :where(kbd):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          font-weight: 500;
          font-family: inherit;
          color: var(--tw-prose-kbd);
          box-shadow:
            0 0 0 1px rgb(var(--tw-prose-kbd-shadows) / 10%),
            0 3px 0 rgb(var(--tw-prose-kbd-shadows) / 10%);
          font-size: 0.875em;
          border-radius: 0.3125rem;
          padding-top: 0.1875em;
          padding-inline-end: 0.375em;
          padding-bottom: 0.1875em;
          padding-inline-start: 0.375em;
        }

        :where(code):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-code);
          font-weight: 600;
          font-size: 0.875em;
        }

        :where(code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::before {
          content: "`";
        }

        :where(code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::after {
          content: "`";
        }

        :where(a code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(h1 code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(h2 code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
          font-size: 0.875em;
        }

        :where(h3 code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
          font-size: 0.9em;
        }

        :where(h4 code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(blockquote code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(thead th code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: inherit;
        }

        :where(pre):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          color: var(--tw-prose-pre-code);
          background-color: var(--tw-prose-pre-bg);
          overflow-x: auto;
          font-weight: 400;
          font-size: 0.875em;
          line-height: 1.7142857;
          margin-top: 1.7142857em;
          margin-bottom: 1.7142857em;
          border-radius: 0.375rem;
          padding-top: 0.8571429em;
          padding-inline-end: 1.1428571em;
          padding-bottom: 0.8571429em;
          padding-inline-start: 1.1428571em;
        }

        :where(pre code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          background-color: transparent;
          border-width: 0;
          border-radius: 0;
          padding: 0;
          font-weight: inherit;
          color: inherit;
          font-size: inherit;
          font-family: inherit;
          line-height: inherit;
        }

        :where(pre code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::before {
          content: none;
        }

        :where(pre code):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          )::after {
          content: none;
        }

        :where(table):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          width: 100%;
          table-layout: auto;
          margin-top: 2em;
          margin-bottom: 2em;
          font-size: 0.875em;
          line-height: 1.7142857;
        }

        :where(thead):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          border-bottom-width: 1px;
          border-bottom-color: var(--tw-prose-th-borders);
        }

        :where(thead th):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: var(--tw-prose-headings);
          font-weight: 600;
          vertical-align: bottom;
          padding-inline-end: 0.5714286em;
          padding-bottom: 0.5714286em;
          padding-inline-start: 0.5714286em;
        }

        :where(tbody tr):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          border-bottom-width: 1px;
          border-bottom-color: var(--tw-prose-td-borders);
        }

        :where(tbody tr:last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          border-bottom-width: 0;
        }

        :where(tbody td):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          vertical-align: baseline;
        }

        :where(tfoot):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          border-top-width: 1px;
          border-top-color: var(--tw-prose-th-borders);
        }

        :where(tfoot td):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          vertical-align: top;
        }

        :where(th, td):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          text-align: start;
        }

        :where(figure > *):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
          margin-bottom: 0;
        }

        :where(figcaption):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          color: var(--tw-prose-captions);
          font-size: 0.875em;
          line-height: 1.4285714;
          margin-top: 0.8571429em;
        }

        --tw-prose-body: oklch(37.3% 0.034 259.733);
        --tw-prose-headings: oklch(21% 0.034 264.665);
        --tw-prose-lead: oklch(44.6% 0.03 256.802);
        --tw-prose-links: oklch(21% 0.034 264.665);
        --tw-prose-bold: oklch(21% 0.034 264.665);
        --tw-prose-counters: oklch(55.1% 0.027 264.364);
        --tw-prose-bullets: oklch(87.2% 0.01 258.338);
        --tw-prose-hr: oklch(92.8% 0.006 264.531);
        --tw-prose-quotes: oklch(21% 0.034 264.665);
        --tw-prose-quote-borders: oklch(92.8% 0.006 264.531);
        --tw-prose-captions: oklch(55.1% 0.027 264.364);
        --tw-prose-kbd: oklch(21% 0.034 264.665);
        --tw-prose-kbd-shadows: NaN NaN NaN;
        --tw-prose-code: oklch(21% 0.034 264.665);
        --tw-prose-pre-code: oklch(92.8% 0.006 264.531);
        --tw-prose-pre-bg: oklch(27.8% 0.033 256.848);
        --tw-prose-th-borders: oklch(87.2% 0.01 258.338);
        --tw-prose-td-borders: oklch(92.8% 0.006 264.531);
        --tw-prose-invert-body: oklch(87.2% 0.01 258.338);
        --tw-prose-invert-headings: #fff;
        --tw-prose-invert-lead: oklch(70.7% 0.022 261.325);
        --tw-prose-invert-links: #fff;
        --tw-prose-invert-bold: #fff;
        --tw-prose-invert-counters: oklch(70.7% 0.022 261.325);
        --tw-prose-invert-bullets: oklch(44.6% 0.03 256.802);
        --tw-prose-invert-hr: oklch(37.3% 0.034 259.733);
        --tw-prose-invert-quotes: oklch(96.7% 0.003 264.542);
        --tw-prose-invert-quote-borders: oklch(37.3% 0.034 259.733);
        --tw-prose-invert-captions: oklch(70.7% 0.022 261.325);
        --tw-prose-invert-kbd: #fff;
        --tw-prose-invert-kbd-shadows: 255 255 255;
        --tw-prose-invert-code: #fff;
        --tw-prose-invert-pre-code: oklch(87.2% 0.01 258.338);
        --tw-prose-invert-pre-bg: rgb(0 0 0 / 50%);
        --tw-prose-invert-th-borders: oklch(44.6% 0.03 256.802);
        --tw-prose-invert-td-borders: oklch(37.3% 0.034 259.733);
        font-size: 1rem;
        line-height: 1.75;

        :where(picture > img):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
          margin-bottom: 0;
        }

        :where(li):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          margin-top: 0.5em;
          margin-bottom: 0.5em;
        }

        :where(ol > li):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-start: 0.375em;
        }

        :where(ul > li):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-start: 0.375em;
        }

        :where(.prose > ul > li p):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0.75em;
          margin-bottom: 0.75em;
        }

        :where(.prose > ul > li > p:first-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 1.25em;
        }

        :where(.prose > ul > li > p:last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-bottom: 1.25em;
        }

        :where(.prose > ol > li > p:first-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 1.25em;
        }

        :where(.prose > ol > li > p:last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-bottom: 1.25em;
        }

        :where(ul ul, ul ol, ol ul, ol ol):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0.75em;
          margin-bottom: 0.75em;
        }

        :where(dl):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          margin-top: 1.25em;
          margin-bottom: 1.25em;
        }

        :where(dd):not(:where([class~="not-prose"], [class~="not-prose"] *)) {
          margin-top: 0.5em;
          padding-inline-start: 1.625em;
        }

        :where(hr + *):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
        }

        :where(h2 + *):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
        }

        :where(h3 + *):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
        }

        :where(h4 + *):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
        }

        :where(thead th:first-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-start: 0;
        }

        :where(thead th:last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-end: 0;
        }

        :where(tbody td, tfoot td):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-top: 0.5714286em;
          padding-inline-end: 0.5714286em;
          padding-bottom: 0.5714286em;
          padding-inline-start: 0.5714286em;
        }

        :where(tbody td:first-child, tfoot td:first-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-start: 0;
        }

        :where(tbody td:last-child, tfoot td:last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          padding-inline-end: 0;
        }

        :where(figure):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 2em;
          margin-bottom: 2em;
        }

        :where(.prose > :first-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-top: 0;
        }

        :where(.prose > :last-child):not(
            :where([class~="not-prose"], [class~="not-prose"] *)
          ) {
          margin-bottom: 0;
        }
      }

      .\!mt-0\.5 {
        margin-top: calc(var(--spacing) * 0.5) !important;
      }

      .-mt-1 {
        margin-top: calc(var(--spacing) * -1);
      }

      .-mt-1\.5 {
        margin-top: calc(var(--spacing) * -1.5);
      }

      .mt-1 {
        margin-top: calc(var(--spacing) * 1);
      }

      .mt-1\.5 {
        margin-top: calc(var(--spacing) * 1.5);
      }

      .mt-2 {
        margin-top: calc(var(--spacing) * 2);
      }

      .mt-4 {
        margin-top: calc(var(--spacing) * 4);
      }

      .mt-auto {
        margin-top: auto;
      }

      .mr-2 {
        margin-right: calc(var(--spacing) * 2);
      }

      .\!mb-0 {
        margin-bottom: calc(var(--spacing) * 0) !important;
      }

      .-mb-10 {
        margin-bottom: calc(var(--spacing) * -10);
      }

      .mb-1 {
        margin-bottom: calc(var(--spacing) * 1);
      }

      .mb-1\.5 {
        margin-bottom: calc(var(--spacing) * 1.5);
      }

      .mb-2 {
        margin-bottom: calc(var(--spacing) * 2);
      }

      .mb-4 {
        margin-bottom: calc(var(--spacing) * 4);
      }

      .\!ml-0 {
        margin-left: calc(var(--spacing) * 0) !important;
      }

      .ml-2 {
        margin-left: calc(var(--spacing) * 2);
      }

      .ml-auto {
        margin-left: auto;
      }

      .line-clamp-1 {
        overflow: hidden;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 1;
        line-clamp: 1;
      }

      .line-clamp-3 {
        overflow: hidden;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 3;
        line-clamp: 3;
      }

      .line-clamp-4 {
        overflow: hidden;
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 4;
        line-clamp: 4;
      }

      .block {
        display: block;
      }

      .flex {
        display: flex;
      }

      .grid {
        display: grid;
      }

      .hidden {
        display: none;
      }

      .inline {
        display: inline;
      }

      .inline-block {
        display: inline-block;
      }

      .inline-flex {
        display: inline-flex;
      }

      .aspect-square {
        aspect-ratio: 1 / 1;
      }

      .h-2 {
        height: calc(var(--spacing) * 2);
      }

      .h-5 {
        height: calc(var(--spacing) * 5);
      }

      .h-8 {
        height: calc(var(--spacing) * 8);
      }

      .h-10 {
        height: calc(var(--spacing) * 10);
      }

      .h-15 {
        height: calc(var(--spacing) * 15);
      }

      .h-\[0\.8lh\] {
        height: 0.8lh;
      }

      .h-\[80vh\] {
        height: 80vh;
      }

      .h-auto {
        height: auto;
      }

      .h-full {
        height: 100%;
      }

      .max-h-\[130px\] {
        max-height: 130px;
      }

      .min-h-20 {
        min-height: calc(var(--spacing) * 20);
      }

      .min-h-\[56px\] {
        min-height: 56px;
      }

      .min-h-\[calc\(80vh-\(300px\)\)\] {
        min-height: calc(80vh - (300px));
      }

      .w-5 {
        width: calc(var(--spacing) * 5);
      }

      .w-8 {
        width: calc(var(--spacing) * 8);
      }

      .w-10 {
        width: calc(var(--spacing) * 10);
      }

      .w-16 {
        width: calc(var(--spacing) * 16);
      }

      .w-48 {
        width: calc(var(--spacing) * 48);
      }

      .w-50 {
        width: calc(var(--spacing) * 50);
      }

      .w-\[1px\] {
        width: 1px;
      }

      .w-auto {
        width: auto;
      }

      .w-fit {
        width: fit-content;
      }

      .w-full {
        width: 100%;
      }

      .w-screen {
        width: 100vw;
      }

      .max-w-3xl {
        max-width: var(--container-3xl);
      }

      .max-w-\[1000px\] {
        max-width: 1000px;
      }

      .max-w-lg {
        max-width: var(--container-lg);
      }

      .max-w-md {
        max-width: var(--container-md);
      }

      .max-w-none {
        max-width: none;
      }

      .min-w-0 {
        min-width: calc(var(--spacing) * 0);
      }

      .min-w-10 {
        min-width: calc(var(--spacing) * 10);
      }

      .min-w-32 {
        min-width: calc(var(--spacing) * 32);
      }

      .min-w-44 {
        min-width: calc(var(--spacing) * 44);
      }

      .flex-1 {
        flex: 1;
      }

      .flex-shrink-0 {
        flex-shrink: 0;
      }

      .shrink-0 {
        flex-shrink: 0;
      }

      .grow {
        flex-grow: 1;
      }

      .origin-center {
        transform-origin: center;
      }

      .-translate-x-1\/2 {
        --tw-translate-x: calc(calc(1 / 2 * 100%) * -1);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .translate-x-4 {
        --tw-translate-x: calc(var(--spacing) * 4);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .-translate-y-1 {
        --tw-translate-y: calc(var(--spacing) * -1);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .-translate-y-1\/2 {
        --tw-translate-y: calc(calc(1 / 2 * 100%) * -1);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .-translate-y-2 {
        --tw-translate-y: calc(var(--spacing) * -2);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .translate-y-0 {
        --tw-translate-y: calc(var(--spacing) * 0);
        translate: var(--tw-translate-x) var(--tw-translate-y);
      }

      .-rotate-90 {
        rotate: calc(90deg * -1);
      }

      .rotate-90 {
        rotate: 90deg;
      }

      .transform {
        transform: var(--tw-rotate-x,) var(--tw-rotate-y,) var(--tw-rotate-z,)
          var(--tw-skew-x,) var(--tw-skew-y,);
      }

      .animate-background {
        animation: var(--animate-background);
      }

      .animate-draw-shield {
        animation: var(--animate-draw-shield);
      }

      .animate-gradient {
        animation: var(--animate-gradient);
      }

      .animate-pulse {
        animation: var(--animate-pulse);
      }

      .animate-slidein {
        animation: var(--animate-slidein);
      }

      .animate-sparkle-sequence {
        animation: var(--animate-sparkle-sequence);
      }

      .cursor-pointer {
        cursor: pointer;
      }

      .resize-none {
        resize: none;
      }

      .flex-col {
        flex-direction: column;
      }

      .flex-row {
        flex-direction: row;
      }

      .flex-wrap {
        flex-wrap: wrap;
      }

      .place-items-center {
        place-items: center;
      }

      .items-center {
        align-items: center;
      }

      .items-end {
        align-items: flex-end;
      }

      .items-start {
        align-items: flex-start;
      }

      .justify-between {
        justify-content: space-between;
      }

      .justify-center {
        justify-content: center;
      }

      .justify-end {
        justify-content: flex-end;
      }

      .justify-start {
        justify-content: flex-start;
      }

      .gap-1 {
        gap: calc(var(--spacing) * 1);
      }

      .gap-2 {
        gap: calc(var(--spacing) * 2);
      }

      .gap-3 {
        gap: calc(var(--spacing) * 3);
      }

      .gap-4 {
        gap: calc(var(--spacing) * 4);
      }

      .space-y-4 {
        :where(& > :not(:last-child)) {
          --tw-space-y-reverse: 0;
          margin-block-start: calc(
            calc(var(--spacing) * 4) * var(--tw-space-y-reverse)
          );
          margin-block-end: calc(
            calc(var(--spacing) * 4) * calc(1 - var(--tw-space-y-reverse))
          );
        }
      }

      .overflow-clip {
        overflow: clip;
      }

      .overflow-hidden {
        overflow: hidden;
      }

      .overflow-visible {
        overflow: visible;
      }

      .overflow-x-auto {
        overflow-x: auto;
      }

      .overflow-y-auto {
        overflow-y: auto;
      }

      .overflow-y-hidden {
        overflow-y: hidden;
      }

      .rounded-3xl {
        border-radius: var(--radius-3xl);
      }

      .rounded-full {
        border-radius: calc(infinity * 1px);
      }

      .rounded-lg {
        border-radius: var(--radius-lg);
      }

      .rounded-md {
        border-radius: var(--radius-md);
      }

      .rounded-none {
        border-radius: 0;
      }

      .rounded-xl {
        border-radius: var(--radius-xl);
      }

      .rounded-t-xl {
        border-top-left-radius: var(--radius-xl);
        border-top-right-radius: var(--radius-xl);
      }

      .rounded-l-md {
        border-top-left-radius: var(--radius-md);
        border-bottom-left-radius: var(--radius-md);
      }

      .rounded-l-none {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
      }

      .rounded-tr-none {
        border-top-right-radius: 0;
      }

      .rounded-b-xl {
        border-bottom-right-radius: var(--radius-xl);
        border-bottom-left-radius: var(--radius-xl);
      }

      .border {
        border-style: var(--tw-border-style);
        border-width: 1px;
      }

      .border-4 {
        border-style: var(--tw-border-style);
        border-width: 4px;
      }

      .border-b {
        border-bottom-style: var(--tw-border-style);
        border-bottom-width: 1px;
      }

      .border-none {
        --tw-border-style: none;
        border-style: none;
      }

      .border-accent-light {
        border-color: var(--color-accent-light);
      }

      .border-blue {
        border-color: var(--color-blue);
      }

      .border-gray-200 {
        border-color: var(--color-gray-200);
      }

      .border-gray-300 {
        border-color: var(--color-gray-300);
      }

      .border-neutral-500\/80 {
        border-color: color-mix(in srgb, oklch(55.6% 0 0) 80%, transparent);

        @supports (color: color-mix(in lab, red, red)) {
          border-color: color-mix(
            in oklab,
            var(--color-neutral-500) 80%,
            transparent
          );
        }
      }

      .border-purple {
        border-color: var(--color-purple);
      }

      .border-text\/50 {
        border-color: color-mix(in srgb, #1b1c1d 50%, transparent);

        @supports (color: color-mix(in lab, red, red)) {
          border-color: color-mix(in oklab, var(--color-text) 50%, transparent);
        }
      }

      .border-transparent {
        border-color: transparent;
      }

      .bg-\[\#2d2d2d\] {
        background-color: #2d2d2d;
      }

      .bg-accent {
        background-color: var(--color-accent);
      }

      .bg-accent-dark {
        background-color: var(--color-accent-dark);
      }

      .bg-accent-light {
        background-color: var(--color-accent-light);
      }

      .bg-base {
        background-color: var(--color-base);
      }

      .bg-blue {
        background-color: var(--color-blue);
      }

      .bg-gray-100 {
        background-color: var(--color-gray-100);
      }

      .bg-red-100 {
        background-color: var(--color-red-100);
      }

      .bg-text {
        background-color: var(--color-text);
      }

      .bg-text-muted {
        background-color: var(--color-text-muted);
      }

      .bg-transparent {
        background-color: transparent;
      }

      .bg-\[linear-gradient\(90deg\,\#217BFE_0\%\,\#078EFB_33\%\,\#AC87EB_67\%\,\#EE4D5D_100\%\)\] {
        background-image: linear-gradient(
          90deg,
          #217bfe 0%,
          #078efb 33%,
          #ac87eb 67%,
          #ee4d5d 100%
        );
      }

      .bg-\[length\:200\%_auto\] {
        background-size: 200% auto;
      }

      .bg-\[length\:_400\%_400\%\] {
        background-size: 400% 400%;
      }

      .bg-clip-text {
        background-clip: text;
      }

      .stroke-\[1\.5px\] {
        stroke-width: 1.5px;
      }

      .p-0 {
        padding: calc(var(--spacing) * 0);
      }

      .p-1 {
        padding: calc(var(--spacing) * 1);
      }

      .p-2 {
        padding: calc(var(--spacing) * 2);
      }

      .p-3 {
        padding: calc(var(--spacing) * 3);
      }

      .p-4 {
        padding: calc(var(--spacing) * 4);
      }

      .p-6 {
        padding: calc(var(--spacing) * 6);
      }

      .p-\[1px\] {
        padding: 1px;
      }

      .px-1 {
        padding-inline: calc(var(--spacing) * 1);
      }

      .px-2 {
        padding-inline: calc(var(--spacing) * 2);
      }

      .px-3 {
        padding-inline: calc(var(--spacing) * 3);
      }

      .px-4 {
        padding-inline: calc(var(--spacing) * 4);
      }

      .py-0\.5 {
        padding-block: calc(var(--spacing) * 0.5);
      }

      .py-1 {
        padding-block: calc(var(--spacing) * 1);
      }

      .py-1\.5 {
        padding-block: calc(var(--spacing) * 1.5);
      }

      .py-2 {
        padding-block: calc(var(--spacing) * 2);
      }

      .py-3 {
        padding-block: calc(var(--spacing) * 3);
      }

      .py-6 {
        padding-block: calc(var(--spacing) * 6);
      }

      .pt-2 {
        padding-top: calc(var(--spacing) * 2);
      }

      .pb-0 {
        padding-bottom: calc(var(--spacing) * 0);
      }

      .pb-1 {
        padding-bottom: calc(var(--spacing) * 1);
      }

      .pb-2 {
        padding-bottom: calc(var(--spacing) * 2);
      }

      .pb-4 {
        padding-bottom: calc(var(--spacing) * 4);
      }

      .pb-12 {
        padding-bottom: calc(var(--spacing) * 12);
      }

      .pb-\[150px\] {
        padding-bottom: 150px;
      }

      .text-center {
        text-align: center;
      }

      .text-start {
        text-align: start;
      }

      .\!font-mono {
        font-family: var(--font-mono) !important;
      }

      .font-base {
        font-family: var(--font-base);
      }

      .font-mono {
        font-family: var(--font-mono);
      }

      .\!text-sm {
        font-size: var(--text-sm) !important;
        line-height: var(--tw-leading, var(--text-sm--line-height)) !important;
      }

      .text-lg {
        font-size: var(--text-lg);
        line-height: var(--tw-leading, var(--text-lg--line-height));
      }

      .text-sm {
        font-size: var(--text-sm);
        line-height: var(--tw-leading, var(--text-sm--line-height));
      }

      .text-xl {
        font-size: var(--text-xl);
        line-height: var(--tw-leading, var(--text-xl--line-height));
      }

      .text-xs {
        font-size: var(--text-xs);
        line-height: var(--tw-leading, var(--text-xs--line-height));
      }

      .text-\[12px\] {
        font-size: 12px;
      }

      .font-bold {
        --tw-font-weight: var(--font-weight-bold);
        font-weight: var(--font-weight-bold);
      }

      .font-medium {
        --tw-font-weight: var(--font-weight-medium);
        font-weight: var(--font-weight-medium);
      }

      .font-semibold {
        --tw-font-weight: var(--font-weight-semibold);
        font-weight: var(--font-weight-semibold);
      }

      .tracking-wide {
        --tw-tracking: var(--tracking-wide);
        letter-spacing: var(--tracking-wide);
      }

      .\!text-text {
        color: var(--color-text) !important;
      }

      .text-base {
        color: var(--color-base);
      }

      .text-blue {
        color: var(--color-blue);
      }

      .text-gray-500 {
        color: var(--color-gray-500);
      }

      .text-gray-800 {
        color: var(--color-gray-800);
      }

      .text-inherit {
        color: inherit;
      }

      .text-purple {
        color: var(--color-purple);
      }

      .text-red-700 {
        color: var(--color-red-700);
      }

      .text-sky-500 {
        color: var(--color-sky-500);
      }

      .text-text {
        color: var(--color-text);
      }

      .text-text-blue {
        color: var(--color-text-blue);
      }

      .text-text-muted {
        color: var(--color-text-muted);
      }

      .text-transparent {
        color: transparent;
      }

      .text-white {
        color: var(--color-white);
      }

      .uppercase {
        text-transform: uppercase;
      }

      .italic {
        font-style: italic;
      }

      .opacity-0 {
        opacity: 0%;
      }

      .opacity-100 {
        opacity: 100%;
      }

      .shadow-md {
        --tw-shadow: 0 4px 6px -1px var(--tw-shadow-color, rgb(0 0 0 / 0.1)),
          0 2px 4px -2px var(--tw-shadow-color, rgb(0 0 0 / 0.1));
        box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow),
          var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow);
      }

      .shadow-sm {
        --tw-shadow: 0 1px 3px 0 var(--tw-shadow-color, rgb(0 0 0 / 0.1)),
          0 1px 2px -1px var(--tw-shadow-color, rgb(0 0 0 / 0.1));
        box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow),
          var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow);
      }

      .backdrop-blur-lg {
        --tw-backdrop-blur: blur(var(--blur-lg));
        -webkit-backdrop-filter: var(--tw-backdrop-blur,)
          var(--tw-backdrop-brightness,) var(--tw-backdrop-contrast,)
          var(--tw-backdrop-grayscale,) var(--tw-backdrop-hue-rotate,)
          var(--tw-backdrop-invert,) var(--tw-backdrop-opacity,)
          var(--tw-backdrop-saturate,) var(--tw-backdrop-sepia,);
        backdrop-filter: var(--tw-backdrop-blur,) var(--tw-backdrop-brightness,)
          var(--tw-backdrop-contrast,) var(--tw-backdrop-grayscale,)
          var(--tw-backdrop-hue-rotate,) var(--tw-backdrop-invert,)
          var(--tw-backdrop-opacity,) var(--tw-backdrop-saturate,)
          var(--tw-backdrop-sepia,);
      }

      .transition {
        transition-property:
          color,
          background-color,
          border-color,
          outline-color,
          text-decoration-color,
          fill,
          stroke,
          --tw-gradient-from,
          --tw-gradient-via,
          --tw-gradient-to,
          opacity,
          box-shadow,
          transform,
          translate,
          scale,
          rotate,
          filter,
          -webkit-backdrop-filter,
          backdrop-filter,
          display,
          visibility,
          content-visibility,
          overlay,
          pointer-events;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-\[height\] {
        transition-property: height;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-\[overlay\,display\,opacity\] {
        transition-property: overlay, display, opacity;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-all {
        transition-property: all;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-colors {
        transition-property: color, background-color, border-color,
          outline-color, text-decoration-color, fill, stroke, --tw-gradient-from,
          --tw-gradient-via, --tw-gradient-to;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-opacity {
        transition-property: opacity;
        transition-timing-function: var(
          --tw-ease,
          var(--default-transition-timing-function)
        );
        transition-duration: var(
          --tw-duration,
          var(--default-transition-duration)
        );
      }

      .transition-discrete {
        transition-behavior: allow-discrete;
      }

      .duration-200 {
        --tw-duration: 200ms;
        transition-duration: 200ms;
      }

      .duration-300 {
        --tw-duration: 300ms;
        transition-duration: 300ms;
      }

      .duration-400 {
        --tw-duration: 400ms;
        transition-duration: 400ms;
      }

      .duration-1000 {
        --tw-duration: 1000ms;
        transition-duration: 1000ms;
      }

      .ease-in-out {
        --tw-ease: var(--ease-in-out);
        transition-timing-function: var(--ease-in-out);
      }

      .ease-out {
        --tw-ease: var(--ease-out);
        transition-timing-function: var(--ease-out);
      }

      .\[animation-duration\:_6s\] {
        animation-duration: 6s;
      }

      .\[scrollbar-color\:transparent_transparent\] {
        scrollbar-color: transparent transparent;
      }

      .group-hover\:opacity-100 {
        &:is(:where(.group):hover *) {
          @media (hover: hover) {
            opacity: 100%;
          }
        }
      }

      .placeholder\:text-text-muted {
        &::placeholder {
          color: var(--color-text-muted);
        }
      }

      .backdrop\:bg-base\/50 {
        &::backdrop {
          background-color: color-mix(in srgb, #f9fafb 50%, transparent);

          @supports (color: color-mix(in lab, red, red)) {
            background-color: color-mix(
              in oklab,
              var(--color-base) 50%,
              transparent
            );
          }
        }
      }

      .backdrop\:backdrop-blur-xs {
        &::backdrop {
          --tw-backdrop-blur: blur(var(--blur-xs));
          -webkit-backdrop-filter: var(--tw-backdrop-blur,)
            var(--tw-backdrop-brightness,) var(--tw-backdrop-contrast,)
            var(--tw-backdrop-grayscale,) var(--tw-backdrop-hue-rotate,)
            var(--tw-backdrop-invert,) var(--tw-backdrop-opacity,)
            var(--tw-backdrop-saturate,) var(--tw-backdrop-sepia,);
          backdrop-filter: var(--tw-backdrop-blur,)
            var(--tw-backdrop-brightness,) var(--tw-backdrop-contrast,)
            var(--tw-backdrop-grayscale,) var(--tw-backdrop-hue-rotate,)
            var(--tw-backdrop-invert,) var(--tw-backdrop-opacity,)
            var(--tw-backdrop-saturate,) var(--tw-backdrop-sepia,);
        }
      }

      .backdrop\:transition-\[overlay\,display\,opacity\] {
        &::backdrop {
          transition-property: overlay, display, opacity;
          transition-timing-function: var(
            --tw-ease,
            var(--default-transition-timing-function)
          );
          transition-duration: var(
            --tw-duration,
            var(--default-transition-duration)
          );
        }
      }

      .backdrop\:transition-discrete {
        &::backdrop {
          transition-behavior: allow-discrete;
        }
      }

      .backdrop\:duration-300 {
        &::backdrop {
          --tw-duration: 300ms;
          transition-duration: 300ms;
        }
      }

      .open\:block {
        &:is([open], :popover-open, :open) {
          display: block;
        }
      }

      .open\:opacity-100 {
        &:is([open], :popover-open, :open) {
          opacity: 100%;
        }
      }

      .hover\:cursor-not-allowed {
        &:hover {
          @media (hover: hover) {
            cursor: not-allowed;
          }
        }
      }

      .hover\:cursor-pointer {
        &:hover {
          @media (hover: hover) {
            cursor: pointer;
          }
        }
      }

      .hover\:bg-accent {
        &:hover {
          @media (hover: hover) {
            background-color: var(--color-accent);
          }
        }
      }

      .hover\:bg-accent-light {
        &:hover {
          @media (hover: hover) {
            background-color: var(--color-accent-light);
          }
        }
      }

      .hover\:bg-base {
        &:hover {
          @media (hover: hover) {
            background-color: var(--color-base);
          }
        }
      }

      .hover\:bg-text-muted {
        &:hover {
          @media (hover: hover) {
            background-color: var(--color-text-muted);
          }
        }
      }

      .hover\:bg-transparent {
        &:hover {
          @media (hover: hover) {
            background-color: transparent;
          }
        }
      }

      .hover\:bg-white {
        &:hover {
          @media (hover: hover) {
            background-color: var(--color-white);
          }
        }
      }

      .hover\:bg-\[linear-gradient\(152deg\,_\#217BFE\,_\#078EFB_42\%\,_\#AC87EB\)\] {
        &:hover {
          @media (hover: hover) {
            background-image: linear-gradient(
              152deg,
              #217bfe,
              #078efb 42%,
              #ac87eb
            );
          }
        }
      }

      .hover\:text-black {
        &:hover {
          @media (hover: hover) {
            color: var(--color-black);
          }
        }
      }

      .hover\:opacity-90 {
        &:hover {
          @media (hover: hover) {
            opacity: 90%;
          }
        }
      }

      .hover\:\[scrollbar-color\:var\(--color-accent\)_var\(--color-base\)\] {
        &:hover {
          @media (hover: hover) {
            scrollbar-color: var(--color-accent) var(--color-base);
          }
        }
      }

      .focus\:z-10 {
        &:focus {
          z-index: 10;
        }
      }

      .focus\:border-blue {
        &:focus {
          border-color: var(--color-blue);
        }
      }

      .focus\:ring-1 {
        &:focus {
          --tw-ring-shadow: var(--tw-ring-inset,) 0 0 0
            calc(1px + var(--tw-ring-offset-width))
            var(--tw-ring-color, currentcolor);
          box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow),
            var(--tw-ring-offset-shadow), var(--tw-ring-shadow),
            var(--tw-shadow);
        }
      }

      .focus\:ring-2 {
        &:focus {
          --tw-ring-shadow: var(--tw-ring-inset,) 0 0 0
            calc(2px + var(--tw-ring-offset-width))
            var(--tw-ring-color, currentcolor);
          box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow),
            var(--tw-ring-offset-shadow), var(--tw-ring-shadow),
            var(--tw-shadow);
        }
      }

      .focus\:ring-blue {
        &:focus {
          --tw-ring-color: var(--color-blue);
        }
      }

      .focus\:ring-text {
        &:focus {
          --tw-ring-color: var(--color-text);
        }
      }

      .focus\:ring-offset-1 {
        &:focus {
          --tw-ring-offset-width: 1px;
          --tw-ring-offset-shadow: var(--tw-ring-inset,) 0 0 0
            var(--tw-ring-offset-width) var(--tw-ring-offset-color);
        }
      }

      .focus\:ring-offset-2 {
        &:focus {
          --tw-ring-offset-width: 2px;
          --tw-ring-offset-shadow: var(--tw-ring-inset,) 0 0 0
            var(--tw-ring-offset-width) var(--tw-ring-offset-color);
        }
      }

      .focus\:outline-none {
        &:focus {
          --tw-outline-style: none;
          outline-style: none;
        }
      }

      .disabled\:pointer-events-none {
        &:disabled {
          pointer-events: none;
        }
      }

      .disabled\:cursor-not-allowed {
        &:disabled {
          cursor: not-allowed;
        }
      }

      .disabled\:text-accent {
        &:disabled {
          color: var(--color-accent);
        }
      }

      .disabled\:text-text {
        &:disabled {
          color: var(--color-text);
        }
      }

      .disabled\:text-text-muted {
        &:disabled {
          color: var(--color-text-muted);
        }
      }

      .disabled\:opacity-20 {
        &:disabled {
          opacity: 20%;
        }
      }

      .disabled\:opacity-50 {
        &:disabled {
          opacity: 50%;
        }
      }

      .disabled\:hover\:bg-base {
        &:disabled {
          &:hover {
            @media (hover: hover) {
              background-color: var(--color-base);
            }
          }
        }
      }

      .disabled\:hover\:bg-text {
        &:disabled {
          &:hover {
            @media (hover: hover) {
              background-color: var(--color-text);
            }
          }
        }
      }

      .disabled\:hover\:bg-transparent {
        &:disabled {
          &:hover {
            @media (hover: hover) {
              background-color: transparent;
            }
          }
        }
      }

      .md\:mx-4 {
        @media (width >=990px) {
          margin-inline: calc(var(--spacing) * 4);
        }
      }

      .md\:hidden {
        @media (width >=990px) {
          display: none;
        }
      }

      .md\:inline {
        @media (width >=990px) {
          display: inline;
        }
      }

      .md\:max-w-\[1000px\] {
        @media (width >=990px) {
          max-width: 1000px;
        }
      }

      .md\:gap-4 {
        @media (width >=990px) {
          gap: calc(var(--spacing) * 4);
        }
      }

      .md\:px-4 {
        @media (width >=990px) {
          padding-inline: calc(var(--spacing) * 4);
        }
      }

      .md\:text-2xl {
        @media (width >=990px) {
          font-size: var(--text-2xl);
          line-height: var(--tw-leading, var(--text-2xl--line-height));
        }
      }

      .md\:text-lg {
        @media (width >=990px) {
          font-size: var(--text-lg);
          line-height: var(--tw-leading, var(--text-lg--line-height));
        }
      }

      .md\:text-xl {
        @media (width >=990px) {
          font-size: var(--text-xl);
          line-height: var(--tw-leading, var(--text-xl--line-height));
        }
      }

      .md\:text-\[16px\] {
        @media (width >=990px) {
          font-size: 16px;
        }
      }

      .sm\:block {
        @media (width >=40rem) {
          display: block;
        }
      }

      .sm\:hidden {
        @media (width >=40rem) {
          display: none;
        }
      }

      .sm\:inline-block {
        @media (width >=40rem) {
          display: inline-block;
        }
      }

      .sm\:h-auto {
        @media (width >=40rem) {
          height: auto;
        }
      }

      .sm\:w-auto {
        @media (width >=40rem) {
          width: auto;
        }
      }

      .sm\:min-w-32 {
        @media (width >=40rem) {
          min-width: calc(var(--spacing) * 32);
        }
      }

      .sm\:p-3 {
        @media (width >=40rem) {
          padding: calc(var(--spacing) * 3);
        }
      }

      .sm\:text-sm {
        @media (width >=40rem) {
          font-size: var(--text-sm);
          line-height: var(--tw-leading, var(--text-sm--line-height));
        }
      }

      .dark\:border-gray-500 {
        @media (prefers-color-scheme: dark) {
          border-color: var(--color-gray-500);
        }
      }

      .dark\:bg-gray-600 {
        @media (prefers-color-scheme: dark) {
          background-color: var(--color-gray-600);
        }
      }

      .dark\:text-gray-100 {
        @media (prefers-color-scheme: dark) {
          color: var(--color-gray-100);
        }
      }

      .dark\:disabled\:opacity-50 {
        @media (prefers-color-scheme: dark) {
          &:disabled {
            opacity: 50%;
          }
        }
      }

      .open\:starting\:opacity-0 {
        &:is([open], :popover-open, :open) {
          @starting-style {
            opacity: 0%;
          }
        }
      }

      .prose-headings\:\!text-text {
        &
          :is(
            :where(h1, h2, h3, h4, h5, h6, th):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          color: var(--color-text) !important;
        }
      }

      .prose-p\:first\:\!mt-2 {
        &
          :is(
            :where(p):not(:where([class~="not-prose"], [class~="not-prose"] *))
          ) {
          &:first-child {
            margin-top: calc(var(--spacing) * 2) !important;
          }
        }
      }

      .prose-a\:\!text-text {
        &
          :is(
            :where(a):not(:where([class~="not-prose"], [class~="not-prose"] *))
          ) {
          color: var(--color-text) !important;
        }
      }

      .prose-strong\:\!text-text {
        &
          :is(
            :where(strong):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          color: var(--color-text) !important;
        }
      }

      .prose-code\:rounded-md {
        &
          :is(
            :where(code):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          border-radius: var(--radius-md);
        }
      }

      .prose-code\:bg-accent {
        &
          :is(
            :where(code):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          background-color: var(--color-accent);
        }
      }

      .prose-code\:px-2 {
        &
          :is(
            :where(code):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          padding-inline: calc(var(--spacing) * 2);
        }
      }

      .prose-code\:text-sm {
        &
          :is(
            :where(code):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          font-size: var(--text-sm);
          line-height: var(--tw-leading, var(--text-sm--line-height));
        }
      }

      .prose-code\:text-text {
        &
          :is(
            :where(code):not(
                :where([class~="not-prose"], [class~="not-prose"] *)
              )
          ) {
          color: var(--color-text);
        }
      }

      .prose-li\:marker\:text-base {
        &
          :is(
            :where(li):not(:where([class~="not-prose"], [class~="not-prose"] *))
          ) {
          & *::marker {
            color: var(--color-base);
          }

          &::marker {
            color: var(--color-base);
          }

          & *::-webkit-details-marker {
            color: var(--color-base);
          }

          &::-webkit-details-marker {
            color: var(--color-base);
          }
        }
      }

      .prose-li\:has-\[span\.animated-finished\]\:marker\:text-text-muted {
        &
          :is(
            :where(li):not(:where([class~="not-prose"], [class~="not-prose"] *))
          ) {
          &:has(*:is(span.animated-finished)) {
            & *::marker {
              color: var(--color-text-muted);
            }

            &::marker {
              color: var(--color-text-muted);
            }

            & *::-webkit-details-marker {
              color: var(--color-text-muted);
            }

            &::-webkit-details-marker {
              color: var(--color-text-muted);
            }
          }
        }
      }

      .prose-li\:has-\[\>a\>span\.animated-finished\]\:marker\:text-text-muted {
        &
          :is(
            :where(li):not(:where([class~="not-prose"], [class~="not-prose"] *))
          ) {
          &:has(> a > span.animated-finished) {
            & *::marker {
              color: var(--color-text-muted);
            }

            &::marker {
              color: var(--color-text-muted);
            }

            & *::-webkit-details-marker {
              color: var(--color-text-muted);
            }

            &::-webkit-details-marker {
              color: var(--color-text-muted);
            }
          }
        }
      }
    }

    :host {
      --tw-border-style: solid;
      --tw-font-weight: initial;
      --tw-tracking: initial;
      --tw-shadow: 0 0 #0000;
      --tw-shadow-color: initial;
      --tw-inset-shadow: 0 0 #0000;
      --tw-inset-shadow-color: initial;
      --tw-ring-color: initial;
      --tw-ring-shadow: 0 0 #0000;
      --tw-inset-ring-color: initial;
      --tw-inset-ring-shadow: 0 0 #0000;
      --tw-ring-inset: initial;
      --tw-ring-offset-width: 0px;
      --tw-ring-offset-color: #fff;
      --tw-ring-offset-shadow: 0 0 #0000;

      ::-webkit-scrollbar {
        width: 10px;
      }

      ::-webkit-scrollbar-track {
        background: transparent;
      }

      ::-webkit-scrollbar-thumb {
        background: var(--color-accent);
        border-radius: 5px;
      }

      ::-webkit-scrollbar-thumb:hover {
        background: var(--color-accent-light);
      }

      ::-webkit-scrollbar-thumb:hover {
        cursor: pointer;
      }
    }

    @layer components {
      .card {
        border: 1px solid var(--color-text-muted);
        background-color: var(--color-accent);
        padding: 1rem;
        display: flex;
        border-radius: 0.75rem;
        flex-direction: column;
        gap: 0.5rem;
      }

      .badge {
        width: fit-content;
        border: 1px solid var(--color-text-muted);
        background-color: var(--color-accent);
        padding: 0.5rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text);
        border-radius: 9999px;
      }

      .btn {
        background-color: var(--color-text);
        transition: opacity 0.15s ease-in-out;
      }

      .btn:hover {
        opacity: 0.9;
        cursor: pointer;
      }

      .btn {
        display: flex;
        justify-content: center;
        color: var(--color-base);
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.75rem;
        outline: none;
        box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
      }

      .btn:focus {
        outline: none;
        box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
      }

      .btn:active {
        animation: button-pop 0.4s ease-out;
      }

      .token.comment,
      .token.block-comment,
      .token.prolog,
      .token.doctype,
      .token.cdata {
        color: #999;
      }

      .token.punctuation {
        color: #ccc;
      }

      .token.tag,
      .token.attr-name,
      .token.namespace,
      .token.deleted {
        color: #e2777a;
      }

      .token.function-name {
        color: #6196cc;
      }

      .token.boolean,
      .token.number,
      .token.function {
        color: #f08d49;
      }

      .token.property,
      .token.class-name,
      .token.constant,
      .token.symbol {
        color: #f8c555;
      }

      .token.selector,
      .token.important,
      .token.atrule,
      .token.keyword,
      .token.builtin {
        color: #cc99cd;
      }

      .token.string,
      .token.char,
      .token.attr-value,
      .token.regex,
      .token.variable {
        color: #7ec699;
      }

      .token.operator,
      .token.entity,
      .token.url {
        color: #67cdcc;
      }

      .token.important,
      .token.bold {
        font-weight: bold;
      }

      .token.italic {
        font-style: italic;
      }

      .token.entity {
        cursor: help;
      }

      .token.inserted {
        color: green;
      }
    }

    .open\:opacity-100 {
      opacity: 1;
    }

    .placeholder\:text-text-muted {
      color: var(--color-text-muted);
    }

    .focus\:outline-none {
      outline: none;
    }

    @property --tw-translate-x {
      syntax: "*";
      inherits: false;
      initial-value: 0;
    }

    @property --tw-translate-y {
      syntax: "*";
      inherits: false;
      initial-value: 0;
    }

    @property --tw-translate-z {
      syntax: "*";
      inherits: false;
      initial-value: 0;
    }

    @property --tw-rotate-x {
      syntax: "*";
      inherits: false;
    }

    @property --tw-rotate-y {
      syntax: "*";
      inherits: false;
    }

    @property --tw-rotate-z {
      syntax: "*";
      inherits: false;
    }

    @property --tw-skew-x {
      syntax: "*";
      inherits: false;
    }

    @property --tw-skew-y {
      syntax: "*";
      inherits: false;
    }

    @property --tw-space-y-reverse {
      syntax: "*";
      inherits: false;
      initial-value: 0;
    }

    @property --tw-border-style {
      syntax: "*";
      inherits: false;
      initial-value: solid;
    }

    @property --tw-font-weight {
      syntax: "*";
      inherits: false;
    }

    @property --tw-tracking {
      syntax: "*";
      inherits: false;
    }

    @property --tw-shadow {
      syntax: "*";
      inherits: false;
      initial-value: 0 0 #0000;
    }

    @property --tw-shadow-color {
      syntax: "*";
      inherits: false;
    }

    @property --tw-shadow-alpha {
      syntax: "<percentage>";
      inherits: false;
      initial-value: 100%;
    }

    @property --tw-inset-shadow {
      syntax: "*";
      inherits: false;
      initial-value: 0 0 #0000;
    }

    @property --tw-inset-shadow-color {
      syntax: "*";
      inherits: false;
    }

    @property --tw-inset-shadow-alpha {
      syntax: "<percentage>";
      inherits: false;
      initial-value: 100%;
    }

    @property --tw-ring-color {
      syntax: "*";
      inherits: false;
    }

    @property --tw-ring-shadow {
      syntax: "*";
      inherits: false;
      initial-value: 0 0 #0000;
    }

    @property --tw-inset-ring-color {
      syntax: "*";
      inherits: false;
    }

    @property --tw-inset-ring-shadow {
      syntax: "*";
      inherits: false;
      initial-value: 0 0 #0000;
    }

    @property --tw-ring-inset {
      syntax: "*";
      inherits: false;
    }

    @property --tw-ring-offset-width {
      syntax: "<length>";
      inherits: false;
      initial-value: 0px;
    }

    @property --tw-ring-offset-color {
      syntax: "*";
      inherits: false;
      initial-value: #fff;
    }

    @property --tw-ring-offset-shadow {
      syntax: "*";
      inherits: false;
      initial-value: 0 0 #0000;
    }

    @property --tw-backdrop-blur {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-brightness {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-contrast {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-grayscale {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-hue-rotate {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-invert {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-opacity {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-saturate {
      syntax: "*";
      inherits: false;
    }

    @property --tw-backdrop-sepia {
      syntax: "*";
      inherits: false;
    }

    @property --tw-duration {
      syntax: "*";
      inherits: false;
    }

    @property --tw-ease {
      syntax: "*";
      inherits: false;
    }

    @keyframes pulse {
      50% {
        opacity: 0.5;
      }
    }

    @keyframes draw-shield {
      0% {
        stroke-dashoffset: 800;
        fill-opacity: 0;
        opacity: 0;
      }

      10% {
        stroke-dashoffset: 0;
        fill-opacity: 0;
        opacity: 1;
      }

      20% {
        stroke-dashoffset: 0;
        fill-opacity: 1;
      }

      80% {
        stroke-dashoffset: 0;
        fill-opacity: 1;
        opacity: 1;
      }

      90% {
        stroke-dashoffset: 0;
        fill-opacity: 0;
        opacity: 0;
      }

      100% {
        stroke-dashoffset: 800;
        fill-opacity: 0;
        opacity: 0;
      }
    }

    @keyframes sparkle-sequence {
      0%,
      20% {
        opacity: 0;
        transform: scale(0.5);
      }

      30% {
        opacity: 1;
        transform: scale(1) rotate(0deg);
      }

      70% {
        transform: scale(1) rotate(360deg);
      }

      80% {
        opacity: 1;
        transform: scale(1) rotate(360deg);
      }

      90% {
        opacity: 0;
        transform: scale(0.5) rotate(360deg);
      }

      100% {
        opacity: 0;
        transform: scale(0.5) rotate(360deg);
      }
    }

    @keyframes animatedgradient {
      0% {
        background-position: 0% 50%;
      }

      50% {
        background-position: 100% 50%;
      }

      100% {
        background-position: 0% 50%;
      }
    }

    @keyframes background-move {
      0%,
      100% {
        background-position: 0% 50%;
      }

      50% {
        background-position: 100% 50%;
      }
    }

    @keyframes button-pop {
      0% {
        transform: scale(0.99);
      }

      40% {
        transform: scale(1.01);
      }

      to {
        transform: scale(1);
      }
    }

    @keyframes slidein {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @layer properties {
      @supports ((-webkit-hyphens: none) and (not (margin-trim: inline))) or
        ((-moz-orient: inline) and (not (color: rgb(from red r g b)))) {
        *,
        ::before,
        ::after,
        ::backdrop {
          --tw-translate-x: 0;
          --tw-translate-y: 0;
          --tw-translate-z: 0;
          --tw-rotate-x: initial;
          --tw-rotate-y: initial;
          --tw-rotate-z: initial;
          --tw-skew-x: initial;
          --tw-skew-y: initial;
          --tw-space-y-reverse: 0;
          --tw-border-style: solid;
          --tw-font-weight: initial;
          --tw-tracking: initial;
          --tw-shadow: 0 0 #0000;
          --tw-shadow-color: initial;
          --tw-shadow-alpha: 100%;
          --tw-inset-shadow: 0 0 #0000;
          --tw-inset-shadow-color: initial;
          --tw-inset-shadow-alpha: 100%;
          --tw-ring-color: initial;
          --tw-ring-shadow: 0 0 #0000;
          --tw-inset-ring-color: initial;
          --tw-inset-ring-shadow: 0 0 #0000;
          --tw-ring-inset: initial;
          --tw-ring-offset-width: 0px;
          --tw-ring-offset-color: #fff;
          --tw-ring-offset-shadow: 0 0 #0000;
          --tw-backdrop-blur: initial;
          --tw-backdrop-brightness: initial;
          --tw-backdrop-contrast: initial;
          --tw-backdrop-grayscale: initial;
          --tw-backdrop-hue-rotate: initial;
          --tw-backdrop-invert: initial;
          --tw-backdrop-opacity: initial;
          --tw-backdrop-saturate: initial;
          --tw-backdrop-sepia: initial;
          --tw-duration: initial;
          --tw-ease: initial;
        }
      }
    }
  }
</style>
