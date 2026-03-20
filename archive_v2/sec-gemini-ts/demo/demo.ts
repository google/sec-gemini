/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
To run this demo run the following command:
Linux/Mac: `SEC_GEMINI_API_KEY="YOUR_ACTUAL_API_KEY" npm run demo`
Windows CMD: `set SEC_GEMINI_API_KEY=YOUR_ACTUAL_API_KEY && npm run demo`
*/

import SecGemini, { Message, MessageTypeEnum, Streamer } from "../src/index"; // Import Streamer type

// --- Configuration ---
// Read API Key from environment variable
const API_KEY = process.env.SEC_GEMINI_API_KEY;

// Check if API Key was provided
if (!API_KEY) {
    console.error("Error: API Key not provided.");
    console.error("Please set the SEC_GEMINI_API_KEY environment variable.");
    console.error('Example (Mac/Linux): SEC_GEMINI_API_KEY="YOUR_ACTUAL_API_KEY" npm run demo');
    console.error('Example (Windows CMD): set SEC_GEMINI_API_KEY=your_key_here && npm run demo');
    console.error('Example (PowerShell): $env:SEC_GEMINI_API_KEY="your_key_here" && npm run demo');
    process.exit(1); // Exit the script with an error code
}

// --- Demo Settings ---
const QUERY = "What are google.com MX servers?";
const SESSION_TTL = 600; // 10mn TTL for demo session
const SESSION_NAME = "Sec-Gemini SDK Demo Session";
const SESSION_DESCRIPTION = `Test session created from Sec-Gemini TS SDK demo on ${new Date().toISOString()}`;
const STREAM_WAIT_TIME_MS = 20000; // Keep script alive for 20s during streaming

// --- Callback Definitions ---
let streamClosed = false; // Flag to signal when the stream is done

function onStreamMessage(message: Message): void {
  switch (message.message_type) {
    case MessageTypeEnum.RESULT:
      // In a real app, append content to UI or process result
      process.stdout.write(message.content || ""); // Write content directly to see streaming effect
      break;
    case MessageTypeEnum.UPDATE:
       // Optional: Display thinking indicators or status updates
      console.debug(`\n[Stream UPDATE]: ${message.content || '(Agent Update)'}`);
      break;
    case MessageTypeEnum.THINKING:
        console.debug("\n[Stream THINKING]...");
        break;
    case MessageTypeEnum.ERROR:
        console.error(`\n[Stream ERROR]: ${message.status_code} - ${message.status_message}`);
        break;
    default:
      // console.debug(`\n[Stream Other]: Type=${message.message_type}`); // Log other types if needed
      break;
  }
   // Detect a potential end-of-stream signal (adjust based on actual protocol)
   // This is just an example; the actual signal might be a specific message type or status code.
   if (message.state === 'answering' && message.status_code === 200 && message.message_type === 'result' && !message.content) {
      // This condition might need adjustment based on how the stream *actually* signals completion.
      // For now, we'll rely on the timeout, but a proper end signal is better.
      // console.log("\n[Stream potentially finished based on message content/state]");
   }
}

function onStreamOpen(): void {
    console.log("\n[Stream Status]: Connection opened.");
}

function onStreamError(error: Error): void {
    console.error("\n[Stream Status]: Error occurred:", error.message);
    streamClosed = true; // Signal closure on error
}

function onStreamClose(): void {
    console.log("\n[Stream Status]: Connection closed.");
    streamClosed = true; // Signal closure
}


// --- Main Async Function ---
(async () => {
  console.log("Initializing Sec-Gemini SDK...");
  let secGemini: SecGemini;
  try {
    secGemini = await SecGemini.create(API_KEY);
    console.log("SDK Initialized Successfully.");
    const user = secGemini.getUser();
    const stableModel = secGemini.getStableModel();
    console.log(`User ID: ${user?.id}, Org ID: ${user?.org_id}`);
    console.log(`Using Stable Model: ${stableModel?.model_string || 'Not Available'}`);
  } catch (error) {
    console.error("SDK Initialization Failed:", error);
    return;
  }

  // --- Create a New Session ---
  let session: import("../src/index").InteractiveSession;
  try {
    console.log(`Creating new session ('${SESSION_NAME}')...`);
    session = await secGemini.createSession({
      ttl: SESSION_TTL,
      name: SESSION_NAME,
      description: SESSION_DESCRIPTION,
      logSession: true,
      model: 'stable',
    });
    console.log(`Session created successfully. ID: ${session.id}`);
    console.log(`Session Name: ${session.name}`);
  } catch (error) {
    console.error("Failed to create session:", error);
    return;
  }

  // --- Perform a Standard Generation Request ---
  try {
    console.log(`\n--- Standard Generation Request ---`);
    console.log(`Sending prompt: "${QUERY}"`);
    const response = await session.generate(QUERY);
    console.log(`Generation Response Received (${response.usage?.total_tokens || 0} tokens):`);
    for (const message of response.messages || []) {
      if (message.message_type === MessageTypeEnum.RESULT && message.content) {
        console.log("--- RESULT ---");
        console.log(message.content);
        console.log("--------------");
      }
    }
  } catch (error) {
    console.error("Standard Generation request failed:", error);
  }


  // --- Streaming Request ---
  let streamerInstance: Streamer | null = null;
  console.log(`\n--- Streaming Request ---`);
  console.log(`Sending prompt: "${QUERY}"`);
  try {
    // 1. Get the streamer instance (connects the WebSocket)
    streamerInstance = await session.streamer( // Use the class defined in index.ts
        onStreamMessage,
        onStreamOpen,
        onStreamError,
        onStreamClose
    );
    console.log("[Stream Status]: Streamer instance created, WebSocket connected.");

    // 2. Send the initial message now that the connection is open
    await streamerInstance.send(QUERY);
    console.log("[Stream Status]: Initial prompt sent. Waiting for messages...");
    process.stdout.write("\nStream Output: "); // Prefix for streamed content

    // 3. Keep the script alive to receive messages (Node.js specific)
    // In a real app (UI or long-running service), the event loop handles this.
    // We'll wait for a fixed time or until the onStreamClose callback sets the flag.
    await new Promise<void>(resolve => {
        const checkInterval = setInterval(() => {
            if (streamClosed) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 500); // Check every 500ms

        // Fallback timeout
        setTimeout(() => {
             if (!streamClosed) {
                console.log(`\n[Stream Status]: Reached timeout (${STREAM_WAIT_TIME_MS}ms), closing stream manually.`);
                clearInterval(checkInterval);
                streamerInstance?.close(); // Attempt graceful close
                resolve();
             }
        }, STREAM_WAIT_TIME_MS);
    });
     console.log("\n[Stream Status]: Finished waiting for stream.");


  } catch (error) {
      console.error("[Stream Status]: Streaming request failed:", error);
      // Ensure close flag is set if an error occurs during setup/send
      streamClosed = true;
  } finally {
      // Ensure the stream is closed if it was opened, even if errors occurred later
      if (streamerInstance && !streamClosed) {
           console.log("\n[Stream Status]: Closing stream in finally block.");
           streamerInstance.close();
      }
  }
  console.log("\nDemo done.");

})(); // Run the async function
