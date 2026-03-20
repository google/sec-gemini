---
title: Simple Chatbot with Vanilla JavaScript and SecGemini
description: This guide shows you how to build a basic chatbot using the SecGemini SDK with vanilla JavaScript
---

## Prerequisites

To follow this guide, you'll need:

- An **API key** for the SecGemini.
- A basic understanding of **HTML, CSS, and JavaScript**.

## Step 1: Include the SecGemini SDK

First, you need to include the SecGemini SDK in your HTML file. If you've installed it via npm, you'll likely need a build process (like Webpack, Parcel, Rollup, or Vite) to bundle it. For simplicity, we'll assume you have a way to access the `SecGemini` object globally.

A straightforward way to set this up is to create a new npm project. Navigate to your desired directory and run `npm init`, then `npm install sec-gemini parcel`.

Here's an example `package.json` configuration:

### `package.json`

```json
{
  "name": "test",
  "version": "1.0.0",
  "description": "",
  "license": "ISC",
  "author": "",
  "type": "module",
  "scripts": {
    "start": "parcel index.html",
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "dependencies": {
    "parcel": "^2.15.2",
    "sec-gemini": "^1.1.1"
  },
  "alias": {
    "sec-gemini": "./node_modules/sec-gemini/dist/index.mjs"
  }
}
```

Next, add the following files to your project and then run `npm start` in your terminal.

### `index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Simple Chat</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <script type="module" src="script.js"></script>

  <body>
    <h1>Simple Chat</h1>

    <div id="api-key-container" class="container">
      <h3>Enter API Key</h3>
      <div class="input-row">
        <input
          type="password"
          id="api-key-input-field"
          placeholder="Enter your API key"
        />
        <button id="save-api-key-button">Connect</button>
      </div>
    </div>

    <div id="chat-container" class="container">
      <h3>Chat</h3>
      <div id="messages-container"></div>
      <div class="input-row">
        <input
          type="text"
          id="input-field"
          placeholder="Type your message..."
        />
        <button id="send-button">Send</button>
      </div>
    </div>
  </body>
</html>
```

### `script.js`

```js
import SecGemini from "sec-gemini";

document.addEventListener("DOMContentLoaded", () => {
  const apiKeyInput = document.getElementById("api-key-input-field");
  const saveApiKeyButton = document.getElementById("save-api-key-button");
  const messagesContainer = document.getElementById("messages-container");
  const inputField = document.getElementById("input-field");
  const sendButton = document.getElementById("send-button");

  let secGemini = null;
  let session = null;
  let streamer = null;
  let messages = ["How can I help you today?"];

  function renderMessages() {
    messagesContainer.innerHTML = "";
    messages.forEach((message) => {
      const messageDiv = document.createElement("div");
      messageDiv.classList.add("message");
      messageDiv.textContent = message;
      messagesContainer.appendChild(messageDiv);
    });
  }

  function onMessage(message) {
    if (message.content) {
      messages.push(message.content);
      renderMessages();
    }
  }

  async function saveApiKey() {
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) return;

    try {
      secGemini = await SecGemini.create(apiKey);

      session = await secGemini.createSession({
        ttl: 3600,
        name: "Simple Chat",
        logSession: true,
        model: "stable",
      });

      streamer = await session.streamer(onMessage);

      document.getElementById("api-key-container").style.display = "none";
      document.getElementById("chat-container").style.display = "block";
    } catch (error) {
      console.error("Failed to initialize:", error);
      alert("Invalid API key or connection failed");
    }
  }

  function sendMessage() {
    const message = inputField.value.trim();
    if (message.length >= 3 && streamer) {
      messages.push(message);
      renderMessages();
      streamer.send(message);
      inputField.value = "";
    }
  }

  // Event listeners
  saveApiKeyButton.addEventListener("click", saveApiKey);
  sendButton.addEventListener("click", sendMessage);

  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendMessage();
      e.preventDefault();
    }
  });

  // Initial render
  renderMessages();
});
```

### `style.css` (Bonus Styles)

```css
body {
  font-family: Arial, sans-serif;
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
}

.container {
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

input,
button {
  padding: 10px;
  margin: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  background: #007bff;
  color: white;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

#messages-container {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
  padding: 10px;
  margin: 10px 0;
  background: #f9f9f9;
}

.message {
  margin: 5px 0;
  padding: 5px;
  background: white;
  border-radius: 4px;
}

#chat-container {
  display: none;
}

.input-row {
  display: flex;
  gap: 10px;
}

.input-row input {
  flex: 1;
}
```

## What Next?

You can significantly improve your chatbot's user experience by adding visual feedback and differentiating message types using the SecGemini SDK.

### Visual Feedback: Loading Spinners

To address the lack of visual feedback when a message is sent, implement a **loading spinner**.

1.  **CSS:** Define a CSS class for your spinner in `style.css`.
2.  **`sendMessage` function:**
    - After `streamer.send(message);`, enable a loading state.
    - Disable the `sendButton` and `inputField`.
    - Display a spinner element (e.g., within `messagesContainer` or next to the `inputField`).
3.  **`onMessage` callback:**
    - Once the response is received and rendered, disable the loading state.
    - Re-enable the input elements.
    - Hide the spinner.

This provides immediate reassurance to the user that their message is being processed.

### Differentiating Message Types

Leverage `message.message_type` values (e.g., 'user', 'bot', 'system', 'error') to apply distinct styles to messages, enhancing readability and comprehension.

1.  **CSS:** Expand your `style.css` with definitions for new classes:
    - `user-message`: For user input (distinct background, right-aligned).
    - `bot-message`: For AI responses (different background, left-aligned).
    - `error-message`: For system errors (e.g., red text, warning icon).
    - `system-message`: For informative messages (e.g., centered, neutral color).
2.  **`renderMessages` and `onMessage` functions:** Modify these functions to check `message.message_type` and dynamically add the appropriate CSS class to the `messageDiv` elements.

These enhancements create a more intuitive and professional chatbot application by clearly differentiating who is speaking and what type of information is being conveyed.

For more detailed information on integrating with SecGemini SDK, refer to the official documentation: [](http://localhost:4321/reference/typescript/)
