---
title: Typescript Example
description: An example of a use case of the sdk.
---

# Simple Chatbot with Vanilla JavaScript and P9SDK

This guide demonstrates how to create a basic chatbot using the P9SDK with vanilla JavaScript. We'll adapt the provided Svelte code to achieve this.

## Prerequisites

- You need an API key for the P9SDK.
- Basic understanding of HTML, CSS, and JavaScript.

## Step 1: Include the P9SDK

First, you need to include the P9SDK in your HTML file. You can do this by adding a `<script>` tag that points to the SDK. If you have installed it via npm, you might need a build process to bundle it, or you can look for a CDN link. For simplicity, let's assume you have a way to access the `P9SDK` object globally.

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Simple Chatbot</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <div id="chatbot-container" class="collapsed">
      <button id="toggle-button" class="toggle-button">
        <svg
          xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
          ></path>
        </svg>
      </button>
      <div id="chat-content" class="chat-content">
        <div class="chat-header">
          <h2>SecGem Chat</h2>
          <button
            id="logout-button"
            class="logout-button"
            aria-label="Logout"
            style="display:none;"
          >
            <svg
              xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
        <div id="api-key-container" class="api-key-container">
          <p>Please enter your P9SDK API key</p>
          <div class="api-key-input">
            <input
              type="password"
              id="api-key-input-field"
              placeholder="Enter your API key"
            />
            <button id="save-api-key-button" disabled>Go</button>
          </div>
          <div
            id="error-banner"
            class="error-banner"
            style="display:none;"
          ></div>
        </div>
        <div
          id="messages-container"
          class="messages-container"
          style="display:none;"
        >
          <div class="message assistant-message" id="initial-assistant-message">
            <div class="message-header"><strong>Assistant</strong></div>
            <div class="message-content">How can I help you today?</div>
          </div>
        </div>
        <div id="input-container" class="input-container" style="display:none;">
          <textarea
            id="input-field"
            placeholder="Type your message..."
          ></textarea>
          <button id="send-button" aria-label="input" disabled>
            <svg
              xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
        <div
          id="chat-error-banner"
          class="error-banner"
          style="display:none;"
        ></div>
      </div>
    </div>
    <script src="script.js"></script>
  </body>
</html>
```

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const chatbotContainer = document.getElementById("chatbot-container");
  const toggleButton = document.getElementById("toggle-button");
  const apiKeyInput = document.getElementById("api-key-input-field");
  const saveApiKeyButton = document.getElementById("save-api-key-button");
  const apiKeyContainer = document.getElementById("api-key-container");
  const messagesContainer = document.getElementById("messages-container");
  const inputField = document.getElementById("input-field");
  const sendButton = document.getElementById("send-button");
  const errorBanner = document.getElementById("error-banner");
  const chatErrorBanner = document.getElementById("chat-error-banner");
  const logoutButton = document.getElementById("logout-button");
  const initialAssistantMessage = document.getElementById(
    "initial-assistant-message"
  );

  let apiKey = localStorage.getItem("p9_api_key") || "";
  let isKeySet = !!apiKey;
  let isLoading = false;
  let errorMessage = "";
  let isChatExpanded = false;
  let p9 = null;
  let session = null;
  let streamer = null;
  let messages = [
    {
      id: "initial-assistant-id",
      timestamp: Date.now() / 1000,
      message_type: "info",
      role: "assistant",
      content: "How can I help you today?",
      mime_type: "text/plain",
    },
  ];
  let input_field = "";

  function updateUI() {
    if (isChatExpanded) {
      chatbotContainer.classList.add("expanded");
      chatbotContainer.classList.remove("collapsed");
    } else {
      chatbotContainer.classList.add("collapsed");
      chatbotContainer.classList.remove("expanded");
    }

    if (isKeySet) {
      apiKeyContainer.style.display = "none";
      messagesContainer.style.display = "block";
      inputContainer.style.display = "flex";
      logoutButton.style.display = "block";
    } else {
      apiKeyContainer.style.display = "flex";
      messagesContainer.style.display = "none";
      inputContainer.style.display = "none";
      logoutButton.style.display = "none";
    }

    if (errorMessage) {
      errorBanner.textContent = errorMessage;
      errorBanner.style.display = "block";
    } else {
      errorBanner.style.display = "none";
    }

    sendButton.disabled = isLoading || input_field.trim().length < 3;
    saveApiKeyButton.disabled = isLoading || !apiKeyInput.value.trim();
    apiKeyInput.value = localStorage.getItem("p9_api_key") || ""; // Ensure input reflects stored key
  }

  function onmessage(message) {
    console.log(message);
    switch (message.message_type) {
      case "RESULT":
        messages = [...messages, message].filter(
          (msg) => msg.role !== "system"
        );
        renderMessages();
        break;
      case "INFO":
        if (
          messages.length > 0 &&
          messages[messages.length - 1].role === "system"
        ) {
          messages = messages.slice(0, -1);
        }
        messages = [...messages, message];
        renderMessages();
        break;
      case "ERROR":
        messages = [...messages, message].filter(
          (msg) => msg.role !== "system"
        );
        renderMessages();
        chatErrorBanner.textContent = message.content || "";
        chatErrorBanner.style.display = "block";
        break;
      default:
        console.debug("Received message type", message.message_type);
    }
    scrollToBottom();
  }

  function handleSend() {
    const trimmedInput = inputField.value.trim();
    if (trimmedInput.length >= 3 && streamer) {
      const userMessage = {
        id: crypto.randomUUID(),
        timestamp: Date.now() / 1000,
        message_type: "query",
        role: "user",
        content: trimmedInput,
        mime_type: "text/plain",
      };
      messages = [...messages, userMessage];
      renderMessages();
      streamer.send(trimmedInput);
      inputField.value = "";
      input_field = ""; // Update the JS variable
      scrollToBottom();
    }
  }

  async function saveApiKey() {
    const inputApiKey = apiKeyInput.value.trim();
    if (!inputApiKey) {
      errorMessage = "Please enter a valid API key";
      updateUI();
      return;
    }

    isLoading = true;
    errorMessage = "";
    updateUI();

    try {
      const testP9 = await P9SDK.create(inputApiKey);
      if (!testP9) {
        throw new Error("Failed to initialize SDK with the provided API key");
      }

      localStorage.setItem("p9_api_key", inputApiKey);
      apiKey = inputApiKey;
      isKeySet = true;
      isChatExpanded = true;
      await initializeSDK();
    } catch (error) {
      console.error("API Key validation failed:", error);
      errorMessage = "Invalid API key. Please check and try again.";
    } finally {
      isLoading = false;
      updateUI();
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
        message_type: "info",
        role: "assistant",
        content: "How can I help you today?",
        mime_type: "text/plain",
      },
    ];
    renderMessages();
    updateUI();
    if (streamer) {
      streamer.close();
      streamer = null;
    }
    session = null;
    p9 = null;
  }

  async function initializeSDK() {
    if (!apiKey) return;

    isLoading = true;
    updateUI();
    try {
      p9 = await P9SDK.create(apiKey);
      session = await p9.newSession();
      streamer = await session.streamer(onmessage);
      isLoading = false;
    } catch (error) {
      console.error("Failed to initialize SDK:", error);
      chatErrorBanner.textContent =
        "Failed to initialize chat. Please check your API key and try again.";
      chatErrorBanner.style.display = "block";
      isLoading = false;
      isKeySet = false;
      apiKey = "";
      localStorage.removeItem("p9_api_key");
    } finally {
      updateUI();
    }
  }

  function toggleChat() {
    isChatExpanded = !isChatExpanded;
    updateUI();
    if (isChatExpanded && isKeySet) {
      setTimeout(scrollToBottom, 100);
    }
  }

  function renderMessages() {
    messagesContainer.innerHTML = "";
    messages.forEach((message) => {
      if (message.role !== "system") {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${message.role}-message`);
        const headerDiv = document.createElement("div");
        headerDiv.classList.add("message-header");
        const strong = document.createElement("strong");
        strong.textContent = message.role === "assistant" ? "Assistant" : "You";
        headerDiv.appendChild(strong);
        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        contentDiv.textContent = message.content;
        messageDiv.appendChild(headerDiv);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
      }
    });
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Event Listeners
  toggleButton.addEventListener("click", toggleChat);
  saveApiKeyButton.addEventListener("click", saveApiKey);
  apiKeyInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      saveApiKey();
    }
  });
  sendButton.addEventListener("click", handleSend);
  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSend();
      e.preventDefault();
    }
  });
  logoutButton.addEventListener("click", clearApiKey);

  // Initial Setup
  updateUI();
  if (apiKey) {
    initializeSDK();
  }
  renderMessages();
  setTimeout(scrollToBottom, 500); // Initial scroll
});
```
