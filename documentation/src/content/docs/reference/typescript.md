---
title: Typescript Documentation
description: Sec-Gemini SDK Typescript Documentation
---

## 1. Introduction

The Sec-Gemini SDK provides a streamlined way to interact with Sec-Gemini v1, a new experimental AI model focused on advancing cybersecurity AI frontiers. This Typescript SDK enables developers to access certain methods including:

- Create a session
- Resume an existing session
- Send and Recieve prompts/responses via webhooks

The SDK handles all communication with the Sec-Gemini backend service, allowing you to focus on your application's core functionality while maintaining robust security.

### Core Concepts

- **Initialization:** The SDK is initialized using the `SecGemini.create()` method, which requires an API key and optionally a base URL and websockets URL.
- **Sessions:** The SDK uses the concept of "sessions" (`InteractiveSession`) to manage user interactions. You can create new sessions or resume existing ones.
- **Messages:** Communication within a session is structured using `Message` objects, which include information like the message type, role, and content.
- **Streaming:** The SDK supports bidirectional streaming of messages through the `Streamer` class, enabling real-time communication with the user.
- **HTTP Client:** The `HttpClient` class handles communication with the backend API.

## 2. Installation

### Using npm/yarn

```bash
npm install sec-gemini
# or
yarn add sec-gemini
```

### Importing into your project

```typescript
// ES Modules
import SecGemini from "sec-gemini";
import { MessageTypeEnum, Message } from "sec-gemini";
```

## 3. Set Up

### Initialization

The SDK is initialized with your API key and optional configuration:

```typescript
const apiKey = "your_api_key_here";
const sdk = await SecGemini.create(apiKey: string);
```

## 4. Sessions

### Create a new session

- Purpose: Creates a new interactive session.

- Parameters:
  - `options` (object): Configuration options for the new session
    - `ttl` (number, optional): Time to live for the session in seconds (default: 86400).
    - `name` (string, optional): Human-readable name for the session.
    - `description` (string, optional): Description of the session.
    - `logSession` (boolean, optional): Whether the session can be logged (default: true).
    - `model` (string|ModelInfoInput, optional): Model to use ('stable', 'experimental', or specific ModelInfoInput).
    - `language` (string, optional): ISO language code (default: 'en').
- Return Value: `Promise<InteractiveSession>` - A promise that resolves to a new `InteractiveSession` object.

```typescript
const session = await sdk.createSession({
  ttl: 3600,
  name: "My Session",
  description: "Testing Sec-Gemini SDK",
  model: "stable",
  language: "en",
});
```

### Resume a session

- Purpose: Creates a new interactive session.

- Parameters:
  - `session_id` (string): The id of the session you would like to resume.
- Return Value: `Promise<InteractiveSession>` - A promise that resolves to a new `InteractiveSession` object.

```typescript
const session = await SecGemini.resumeSession("1473-3434-3434-3433");
```

## 5. Communication with the backend

### Create a streamer

- Purpose: Initializes a streamer for bidirectional communication.

- Parameters:

  - `onmessage` (function): Callback function to handle individual messages (`Message`) from the stream.
  - `onresult` (function): Callback function to handle the final result (`Message`) from the stream.
  - Return Value: `Promise<Streamer>` - A promise that resolves to a `Streamer` object.

    ````typescript
         const streamer = await session.streamer(
             (message) => { console.log('Message:', message.content); },
             (result) => { console.log('Result:', result.content); }
         );
         ```
    ````

### Sending a message

- Purpose: Sends data to the stream.
- Parameters:
  - `data` (string): The data to send (e.g., a prompt or request).
- Return Value: `Promise<void>`
- Example:

  ```typescript
  await streamer.send("Tell me about csrf");
  ```

### Attaching a file

- Purpose: Attaches a file to the current session. This allows for uploading files to be used within the session's context.
- Parameters:
  - `fileName` (string): The name of the file to be attached.
  - `mimeType` (MimeType): The MIME type of the file.
  - `fileContent` (string): The content of the file, potentially base64 encoded.
- Return Value: `Promise<void>` - A promise that resolves when the file is successfully attached to the session.

  ```typescript
  await session.attachFile("myFile.txt", "image/jpeg", base64fileContent);
  ```

### Accessing User Information

```typescript
const userInfo = sdk.getUserInfo();
const user = sdk.getUser();
console.log(`Logged in as: ${user?.email}`);
```

### Configuration Defaults

```typescript
const DEFAULT_BASE_URL = "https://api.secgemini.google";
const DEFAULT_WS_URL = "wss://api.secgemini.google";
const DEFAULT_TTL = 86400; // 24 hours in seconds
```

**Note:**

- The `fileContent` is expected to be a string, and it might need to be base64 encoded depending on the file type.
