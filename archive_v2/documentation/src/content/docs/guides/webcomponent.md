---
title: How-To Guide for the Sec-Gemini Web Component
description: Learn how to install on your site
---

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
  is-fullscreen="true"
  api-key=""
  examples='[{"title":"Network Security","prompt":"What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?"},{"title":"Cryptography","prompt":"Explain the concept of public-key cryptography and provide a real-world example of its application."}]'
>
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

- **`session-id`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - If provided, the component will attempt to load an existing session with this ID. If no session is found, a new one will be created.

- **`session-name`** (Optional)

  - **Type:** `string`
  - **Default:** `"New Session"`
  - Sets a display name for the chat session. This is particularly useful for identifying sessions in a user interface or management system.

- **`session-description`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - Provides a brief description for the chat session, offering additional context.

- **`session-prompt`** (Optional)

  - **Type:** `string`
  - **Default:** `""` (empty string)
  - An initial prompt or message to pre-populate the chat with when a new session is started. This can guide the conversation or set the context for the AI.

- **`theme`** (Optional)

  - **Type:** `string`
  - **Accepted Values:** `"light"`, `"dark"`
  - **Default:** `"light"`
  - Determines the visual theme of the chat interface. Set to `"dark"` for a dark mode appearance or `"light"` for a standard light theme.

- **`is-fullscreen`** (Optional)

  - **Type:** `string`
  - **Accepted Values:** `"true"`, `"false"`
  - **Default:** `"false"`
  - Determines whether the webcomponent initially opens in full screen.

- **`examples`** (Optional)

  - **Type:** `string (string representation of a JSON array)`
  - **Accepted Values:** A stringified JSON array of objects, where each object has at least a `title (string)` and a `prompt (string).`
  - **Default:** `null`
  - Lists example prompts on the landing screen

---

You're looking to integrate the `Sec-Gemini` web component into various popular web frameworks using the CDN approach. This is an excellent way to leverage a pre-built component without deep framework-specific bundling.

Here's how you can typically include the `Sec-Gemini` web component in WordPress, Astro, Next.js, and React, focusing on the CDN link.

---

### Framework-Specific Examples

The core idea is to ensure that the `<link>` for the CSS and `<script>` for the JavaScript are loaded in your HTML, and then you can place the `<sec-gem-chat>` tag wherever you want the component to appear.

### 1\. WordPress

Integrating custom HTML and scripts into WordPress can be done in several ways. The simplest for a web component is often through a Custom HTML block or by enqueuing scripts/styles in your theme's `functions.php`.

**Method A: Using a Custom HTML Block (Easiest for specific pages/posts)**

1.  **Edit your Page/Post:** Go to the WordPress editor for the page or post where you want to add the chat.
2.  **Add a "Custom HTML" Block:**

    - Click the `+` icon to add a new block.
    - Search for "Custom HTML" and select it.

3.  **Paste the Code:** Insert the following HTML directly into the Custom HTML block:

```html
<sec-gem-chat
  incognito="true"
  session-id=""
  session-name="TestName"
  session-description="TestDescription"
  session-prompt="You are a senior cybersecurity threat intelligence analyst..."
  theme="dark"
  api-key="..."
  examples='[{"title":"Network Security","prompt":"What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?"},{"title":"Cryptography","prompt":"Explain the concept of public-key cryptography and provide a real-world example of its application."}]'
>
  ></sec-gem-chat
>

<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.css"
/>
<script src="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js"></script>
```

**Considerations for WordPress:**

- **Script/Style Enqueuing (More Robust):** For a more robust and site-wide integration, especially within a custom theme or plugin, you would typically enqueue the script and stylesheet using WordPress's `wp_enqueue_script()` and `wp_enqueue_style()` functions in your theme's `functions.php` file. This ensures proper loading order and caching.
- **HTML Filtering (`wp_kses`):** WordPress might strip unrecognized HTML tags (like `<sec-gem-chat>`) due to its `wp_kses` filtering. If the component doesn't render, you might need to add it to the allowed tags list (this is a more advanced theme/plugin development task). Often, for simple cases like this, it works out of the box in custom HTML blocks or page builders.

### 2\. Astro

Astro components are designed for static site generation and allow you to directly include HTML and scripts. You can place the CDN links in your Astro component's template or a layout.

**Example: `src/pages/index.astro` or `src/layouts/Layout.astro`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sec-Gemini Chat with Astro</title>
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.css"
    />
  </head>
  <body>
    <h1>Welcome to Astro with Sec-Gemini!</h1>
    <sec-gem-chat
      incognito="true"
      session-id=""
      session-name="TestName"
      session-description="TestDescription"
      session-prompt="You are a senior cybersecurity threat intelligence analyst..."
      theme="dark"
      api-key="..."
      examples='[{"title":"Network Security","prompt":"What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?"},{"title":"Cryptography","prompt":"Explain the concept of public-key cryptography and provide a real-world example of its application."}]'
    >
      ></sec-gem-chat
    >

    <script
      is:inline
      src="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js"
    ></script>
  </body>
</html>
```

**Explanation for Astro:**

- Astro compiles to static HTML by default. Standard HTML elements and web components are handled natively.
- You can place the `<link>` and `<script>` tags directly in your `.astro` files (pages or layouts).
- `is:inline` is an Astro directive that forces the script's content to be injected directly into the HTML, rather than linked as an external file.

### 3\. Next.js

Next.js, especially with its App Router (React Server Components), requires careful handling of client-side JavaScript. Web components often need to be rendered client-side or handled as "external" elements.

**Example: `src/app/page.js` (App Router - Client Component for Web Component)**

Because web components typically interact with the DOM and often involve client-side JavaScript, it's best to ensure they are rendered in a Client Component in Next.js.

```javascript
// src/app/page.js or a component file like src/app/components/ChatWrapper.js
"use client"; // This directive marks the file as a Client Component

import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    // Dynamically load the script and stylesheet if they're not already loaded
    // This ensures they are only loaded client-side.
    if (
      typeof window !== "undefined" &&
      !document.querySelector(
        'script[src="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js"]'
      )
    ) {
      const script = document.createElement("script");
      script.src =
        "https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js";
      script.async = true;
      document.body.appendChild(script);

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href =
        "https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.css";
      document.head.appendChild(link);
    }
  }, []); // Run once on client mount

  return (
    <div>
      <h1>Welcome to Next.js with Sec-Gemini!</h1>
      {/* Render the web component. React will treat it as a standard DOM element. */}
      <sec-gem-chat
        incognito="true"
        session-id=""
        session-name="TestName"
        session-description="TestDescription"
        session-prompt="You are a senior cybersecurity threat intelligence analyst..."
        theme="dark"
        api-key="..."
        examples='[{"title":"Network Security","prompt":"What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?"},{"title":"Cryptography","prompt":"Explain the concept of public-key cryptography and provide a real-world example of its application."}]'
      >
        >
      </sec-gem-chat>
    </div>
  );
}
```

**Explanation for Next.js:**

- **`'use client';`**: This directive is crucial for the App Router. It tells Next.js that this component (and its children) should be rendered on the client side. Web components rely on client-side DOM manipulation, so they must be in a Client Component.
- **`useEffect` for Script Loading:** We use `useEffect` to ensure the CDN script and stylesheet are added to the DOM _only on the client_. This avoids issues with Server-Side Rendering (SSR) trying to pre-render a web component that isn't fully defined yet on the server.
- **React treating custom elements:** React (and Next.js) will pass attributes to custom elements as normal HTML attributes. For boolean attributes like `incognito`, React will reflect them correctly.

### 4\. React (Client-Side Rendering)

For a standard Create React App, the simplest way is to put the CDN links directly into your `public/index.html` file, inside the `<head>` or just before the closing `</body>` tag. This makes the web component globally available to your React application.

**`public/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Web site created using create-react-app"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />

    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.css"
    />

    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>

    <script src="https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js"></script>
  </body>
</html>
```

**`src/App.js` (simplified)**

```javascript import React from 'react'; import
"./App.css";
function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>React App with Sec-Gemini</h1>
        <sec-gem-chat
          incognito="true"
          session-id=""
          session-name="TestName"
          session-description="TestDescription"
          session-prompt="You are a senior cybersecurity threat intelligence analyst..."
          theme="dark"
          api-key="..."
          examples='[{"title":"Network Security","prompt":"What are the key differences between a firewall and an intrusion detection system, and how do they work together to secure a network?"},{"title":"Cryptography","prompt":"Explain the concept of public-key cryptography and provide a real-world example of its application."}]'
        >
          >
        </sec-gem-chat>
      </header>
    </div>
  );
}
export default App;
```

## Demo

[see the demo here](/webcomponent)
