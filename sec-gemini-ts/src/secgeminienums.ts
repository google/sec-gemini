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

/**
 * FeedbackType enum generated from type definition.
 */
export enum FeedbackTypeEnum {
    USER_FEEDBACK = 'user_feedback', // Original: user_feedback
    BUG_REPORT = 'bug_report', // Original: bug_report
}

/**
 * MessageType enum generated from type definition.
 */
export enum MessageTypeEnum {
    RESULT = 'result', // Original: result
    SOURCE = 'source', // Original: source
    DEBUG = 'debug', // Original: debug
    INFO = 'info', // Original: info
    ERROR = 'error', // Original: error
    THINKING = 'thinking', // Original: thinking
    UPDATE = 'update', // Original: update
    DELETE = 'delete', // Original: delete
    CONFIRMATION_REQUEST = 'confirmation_request', // Original: confirmation_request
    CONFIRMATION_RESPONSE = 'confirmation_response', // Original: confirmation_response
    QUERY = 'query', // Original: query
}

/**
 * MimeType enum generated from type definition.
 */
export enum MimeTypeEnum {
    TEXT_PLAIN = 'text/plain', // Original: text/plain
    TEXT_MARKDOWN = 'text/markdown', // Original: text/markdown
    TEXT_SERIALIZED_JSON = 'text/serialized-json', // Original: text/serialized-json
    APPLICATION_OCTET_STREAM = 'application/octet-stream', // Original: application/octet-stream
    IMAGE_JPEG = 'image/jpeg', // Original: image/jpeg
    IMAGE_PNG = 'image/png', // Original: image/png
    IMAGE_TIFF = 'image/tiff', // Original: image/tiff
    IMAGE_GIF = 'image/gif', // Original: image/gif
    IMAGE_SVG_XML = 'image/svg+xml', // Original: image/svg+xml
    IMAGE_WEBP = 'image/webp', // Original: image/webp
    IMAGE_AVIF = 'image/avif', // Original: image/avif
    AUDIO_WAV = 'audio/wav', // Original: audio/wav
    AUDIO_MPEG = 'audio/mpeg', // Original: audio/mpeg
    AUDIO_OGG = 'audio/ogg', // Original: audio/ogg
    VIDEO_WEBM = 'video/webm', // Original: video/webm
    VIDEO_MP4 = 'video/mp4', // Original: video/mp4
    TEXT_C = 'text/c', // Original: text/c
    TEXT_C__ = 'text/c++', // Original: text/c++
    TEXT_JAVA = 'text/java', // Original: text/java
    TEXT_RUST = 'text/rust', // Original: text/rust
    TEXT_GO = 'text/go', // Original: text/go
    TEXT_PYTHON = 'text/python', // Original: text/python
    TEXT_PHP = 'text/php', // Original: text/php
    TEXT_PERL = 'text/perl', // Original: text/perl
    TEXT_RUBY = 'text/ruby', // Original: text/ruby
    TEXT_SWIFT = 'text/swift', // Original: text/swift
    TEXT_KOTLIN = 'text/kotlin', // Original: text/kotlin
    TEXT_SCALA = 'text/scala', // Original: text/scala
    TEXT_JAVASCRIPT = 'text/javascript', // Original: text/javascript
    TEXT_TYPESCRIPT = 'text/typescript', // Original: text/typescript
    TEXT_HTML = 'text/html', // Original: text/html
    TEXT_CSS = 'text/css', // Original: text/css
    TEXT_CSV = 'text/csv', // Original: text/csv
    TEXT_XML = 'text/xml', // Original: text/xml
    TEXT_YAML = 'text/yaml', // Original: text/yaml
    TEXT_TOML = 'text/toml', // Original: text/toml
    TEXT_SQL = 'text/sql', // Original: text/sql
    APPLICATION_JSON = 'application/json', // Original: application/json
    APPLICATION_JSONL = 'application/jsonl', // Original: application/jsonl
    APPLICATION_PDF = 'application/pdf', // Original: application/pdf
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // Original: application/vnd.openxmlformats-officedocument.wordprocessingml.document
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // Original: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION = 'application/vnd.openxmlformats-officedocument.presentationml.presentation', // Original: application/vnd.openxmlformats-officedocument.presentationml.presentation
    APPLICATION_MSWORD = 'application/msword', // Original: application/msword
    APPLICATION_VND_MS_EXCEL = 'application/vnd.ms-excel', // Original: application/vnd.ms-excel
    APPLICATION_VND_MS_POWERPOINT = 'application/vnd.ms-powerpoint', // Original: application/vnd.ms-powerpoint
    APPLICATION_RTF = 'application/rtf', // Original: application/rtf
    APPLICATION_VND_OASIS_OPENDOCUMENT_TEXT = 'application/vnd.oasis.opendocument.text', // Original: application/vnd.oasis.opendocument.text
}

/**
 * Role enum generated from type definition.
 */
export enum RoleEnum {
    USER = 'user', // Original: user
    AGENT = 'agent', // Original: agent
    SYSTEM = 'system', // Original: system
}

/**
 * State enum generated from type definition.
 */
export enum StateEnum {
    START = 'start', // Original: start
    QUERY = 'query', // Original: query
    RUNNING_AGENT = 'running_agent', // Original: running_agent
    AGENT_DONE = 'agent_done', // Original: agent_done
    CODING = 'coding', // Original: coding
    CODE_RESULT = 'code_result', // Original: code_result
    CALLING_TOOL = 'calling_tool', // Original: calling_tool
    TOOL_RESULT = 'tool_result', // Original: tool_result
    GENERATING = 'generating', // Original: generating
    ANSWERING = 'answering', // Original: answering
    THINKING = 'thinking', // Original: thinking
    PLANNING = 'planning', // Original: planning
    REVIEWING = 'reviewing', // Original: reviewing
    UNDERSTANDING = 'understanding', // Original: understanding
    RETRIVING = 'retriving', // Original: retriving
    GROUNDING = 'grounding', // Original: grounding
}

/**
 * UserType enum generated from type definition.
 */
export enum UserTypeEnum {
    UI = 'ui', // Original: ui
    USER = 'user', // Original: user
    ADMIN = 'admin', // Original: admin
    SYSTEM = 'system', // Original: system
    SERVICE = 'service', // Original: service
}
