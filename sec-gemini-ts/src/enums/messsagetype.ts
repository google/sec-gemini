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

enum MessageType {
    SESSSION_START = "session_start", //session start
    SESSION_END = "session_end", //session end

    GROUP_START = "group_start", //group of messages start
    GROUP_END = "group_end", //group of messages end

    PROMPT_START = "prompt_start", //user prompt start
    PROMPT = "prompt", //user prompt
    PROMPT_END = "prompt_end", //user

    GENERATION_START = "generation_start", //model generation start
    GENERATION = "generation", //model generated response
    GENERATION_END = "generation_end", //model generation complete

    TOOL_CALL = "tool_call", //tool execution request
    TOOL_RESPONSE = "tool_response", //tool execution response

    INFO = "info" //transient info message only used in streaming
}

export default MessageType;