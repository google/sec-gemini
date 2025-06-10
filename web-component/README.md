## Sec-Gemini Web Component Documentation

The `Sec-Gemini` web component allows for easy integration of Sec-Gemini chat functionality into any website. This documentation outlines how to embed and configure the component using its available attributes.

---

### Installation

There are two primary ways to install the `Sec-Gemini` web component:

#### Via CDN (Content Delivery Network)

This is the quickest way to get started. Include the provided script in your HTML. It's recommended to place it before the closing `</body>` tag.

```html
<body>
  <script src="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js"></script>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.css"
  />
</body>
```

### Usage

Once the component is installed (either via CDN or npm), you can use the `<sec-gem-chat>` tag in your HTML. Customize its behavior by setting the following attributes:

```html
<sec-gem-chat
  incognito="true"
  sessionId=""
  sessionName="My Session"
  sessionDescription="My description"
  sessionPrompt="You are a senior cybersecurity threat intelligence analyst"
  theme="dark"
>
</sec-gem-chat>
```

---

### Attributes

Here's a detailed explanation of each attribute:

- **`incognito`** (Optional)

  - **Type:** `boolean`
  - **Default:** `false`
  - When set to `"true"`, the chat session will operate in incognito mode, meaning the conversation history will not be saved.

- **`sessionId`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - If provided, the component will attempt to load an existing session with this ID. If no session is found, a new one will be created.

- **`sessionName`** (Optional)

  - **Type:** `string`
  - **Default:** `"New Session"`
  - Sets a display name for the chat session. This is particularly useful for identifying sessions in a user interface or management system.

- **`sessionDescription`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - Provides a brief description for the chat session, offering additional context.

- **`sessionPrompt`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - An initial prompt or message to pre-populate the chat with when a new session is started. This can guide the conversation or set the context for the AI.

- **`theme`** (Optional)

  - **Type:** `string`
  - **Accepted Values:** `"light"`, `"dark"`
  - **Default:** `"light"`
  - Determines the visual theme of the chat interface. Set to `"dark"` for a dark mode appearance or `"light"` for a standard light theme.

---