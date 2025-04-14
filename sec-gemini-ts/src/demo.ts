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

// local dev test
import P9SDK from "./index"; // Import from the SDK source
import { MessageTypeEnum, Message } from "./index";

const api_key = "";  // testing key only local
const base_url = "";
const base_wss_url = "";
//const prompt = "What is the capital of France and some basic information about it?";
const prompt = "APT29 targets"
function onmessage(message: Message) {
  switch (message.message_type) {
    case MessageTypeEnum.RESULT:
      console.log(message.content);
      break;
    default:
      console.debug("Received message type", message.message_type);
  }
}

function onresult(message: Message) {
  console.log("onresult", message);
}

(async () => {
  console.log("Intializing Sec-Gemini SDK");
  console.log("API Key: ", api_key);
  const p9sdk = await P9SDK.create(api_key, base_url, base_wss_url);
  const session = await p9sdk.newSession(86400, "", "js-sdk-test");
  console.log("Session ID: ", session.id);


  // regular session first
  session.generate(prompt).then((response) => {
    console.log("Response: (", response?.usage.total_tokens,  ' tokens):\n');
    for (const message of response?.messages || []) {
      if (message.message_type === MessageTypeEnum.RESULT) {
        console.log(message.content);
      }
    }
    return response;
  });



  // bidirectional streaming
  console.log("\n----------\n\nStarting streaming event loop");
  const streamer = await session.streamer(onmessage=onmessage, onresult=
  onresult);
  await streamer.send(prompt);

  /* turn by turn
  console.log("Session ID: ", session.id);
  console.log("Prompt", prompt);
  session.generate(prompt).then((response) => {
    console.log("Response: ", response?.usage.total_tokens,  ' tokens');
    for (const message of response?.messages || []) {
      if (message.message_type === "generation") {
        console.log(message.content);
      }
    }
  });
  */
})();
