<svelte:options customElement="sec-gem-chat" />

<script lang="ts">
  import SecGemini, {
    MessageTypeEnum,
    MimeTypeEnum,
    Streamer,
    type Message,
  } from "sec-gemini";
  import { onMount } from "svelte";
  import libstyles from "./styles.css?inline";
  import MaterialSymbolsAdd2Rounded from "../icons/MaterialSymbolsAdd2Rounded.svelte";
  import PhGreaterThanBold from "../icons/PhGreaterThanBold.svelte";
  import SecGeminiLogo from "../icons/SecGeminiLogo.svelte";
  import MessageList from "./message-list.svelte";
  import Thinking from "./thinking.svelte";
  import MaterialSymbolsClose from "../icons/MaterialSymbolsClose.svelte";
  import MdiIncognito from "../icons/MdiIncognito.svelte";

  let style = "<style>" + libstyles + "</style>";

  const {
    resumeSession,
    theme = "light",
    incognito = true,
    sessionDescription,
    sessionName,
  } = $props();

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
        const mimeType = checkMimeType(file.type);
        if (mimeType === null) {
          console.error("Unsupported MIME type:", file.type);
          return;
        }
        await session.attachFile(file.name, mimeType, fileContent);
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
  function checkMimeType(value: string): MimeTypeEnum | null {
    if (Object.values(MimeTypeEnum).includes(value as MimeTypeEnum)) {
      return value as MimeTypeEnum;
    }
    return null;
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

  onMount(() => {
    if (apiKey) {
      initializeSDK();
    }
    const fontFaces = `
      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-Bold.ttf") format("truetype");
        font-weight: bold;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-BoldItalic.ttf") format("truetype");
        font-weight: bold;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-Medium.ttf") format("truetype");
        font-weight: 500;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-MediumItalic.ttf") format("truetype");
        font-weight: 500;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-Regular.ttf") format("truetype");
        font-weight: normal;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-Bold.ttf") format("truetype");
        font-weight: bold;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-BoldItalic.ttf") format("truetype");
        font-weight: bold;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-Italic.ttf") format("truetype");
        font-weight: normal;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-Medium.ttf") format("truetype");
        font-weight: 500;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-MediumItalic.ttf") format("truetype");
        font-weight: 500;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans Text";
        src: url("/fonts/GoogleSansText-Regular.ttf") format("truetype");
        font-weight: normal;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans";
        src: url("/fonts/GoogleSans-Italic.ttf") format("truetype");
        font-weight: normal;
        font-style: italic;
      }

      @font-face {
        font-family: "Google Sans Mono";
        src: url('https://fonts.gstatic.com/s/googlesansmono/v15/P5sZzYWFYtnZ_Cg-t0Uq_rfivrdYNYhsAg.woff2') format('woff2');
        font-weight: 400;
        font-style: normal;
      }

      @font-face {
        font-family: "Google Sans Mono";
        src: url('https://fonts.gstatic.com/s/googlesansmono/v15/P5sZzYWFYtnZ_Cg-t0Uq_rfivrdYNYhsAg.woff2') format('woff2');
        font-weight: 500;
        font-style: normal;
      }
      @font-face {
        font-family: "Google Sans Code";
        src: url('https://fonts.gstatic.com/s/googlesanscode/v4/pxifyogzv91QhV44Z_GQBHsGf5PuWE5krw.woff2')  format('woff2');
        font-weight: 400 700;
        font-style: normal;
      }
    `;

    const style = document.createElement("style");
    style.textContent = fontFaces;
    document.head.appendChild(style);
  });
</script>

{@html style}
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
    class="chatbot-container fixed inset-0 left-1/2 top-20 z-50 w-screen max-w-3xl h-[80vh] -translate-x-1/2 translate-y-0 opacity-0 transform bg-base p-2 rounded-3xl text-text backdrop:backdrop-blur-xs backdrop:bg-base/50 backdrop-blur-lg transition-[overlay,display,opacity] duration-300 transition-discrete backdrop:transition-[overlay,display,opacity] backdrop:duration-300 backdrop:transition-discrete open:block open:opacity-100 open:starting:opacity-0"
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
                  class="p-2 rounded-full bg-accent-light text-text disabled:opacity-20 disabled:cursor-not-allowed hover:cursor-pointer"
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
                      class={`${isProcessing ? "bg-[linear-gradient(90deg,#217BFE_0%,#078EFB_33%,#AC87EB_67%,#EE4D5D_100%)] text-transparent bg-clip-text animate-gradient bg-[length:200%_auto]" : ""} flex-shrink-0 text-text`}
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

<style>
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
</style>
