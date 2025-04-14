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
 * FeedbackType enum
 */
export enum FeedbackTypeEnum {
    USER_FEEDBACK = 'user_feedback',
    BUG_REPORT = 'bug_report',
}

/**
 * MessageType enum
 */
export enum MessageTypeEnum {
    SESSION_START = 'session_start',
    SESSION_END = 'session_end',
    GROUP_START = 'group_start',
    GROUP_END = 'group_end',
    UPDATE = 'update',
    RESULT = 'result',
    DEBUG = 'debug',
    INFO = 'info',
    ERROR = 'error',
    QUERY = 'query',
}

/**
 * MimeType enum
 */
export enum MimeTypeEnum {
    TEXT_PLAIN = 'text/plain',
    TEXT_MARKDOWN = 'text/markdown',
    TEXT_SERIALIZED_JSON = 'text/serialized-json',
    APPLICATION_OCTET_STREAM = 'application/octet-stream',
    IMAGE_JPEG = 'image/jpeg',
    IMAGE_PNG = 'image/png',
    IMAGE_TIFF = 'image/tiff',
    IMAGE_GIF = 'image/gif',
    IMAGE_SVGPLUSXML = 'image/svg+xml',
    IMAGE_WEBP = 'image/webp',
    IMAGE_AVIF = 'image/avif',
    AUDIO_WAV = 'audio/wav',
    AUDIO_MPEG = 'audio/mpeg',
    AUDIO_OGG = 'audio/ogg',
    VIDEO_WEBM = 'video/webm',
    VIDEO_MP4 = 'video/mp4',
    TEXT_C = 'text/c',
    TEXT_CPLUSPLUS = 'text/c++',
    TEXT_JAVA = 'text/java',
    TEXT_RUST = 'text/rust',
    TEXT_GO = 'text/go',
    TEXT_PYTHON = 'text/python',
    TEXT_PHP = 'text/php',
    TEXT_PERL = 'text/perl',
    TEXT_RUBY = 'text/ruby',
    TEXT_SWIFT = 'text/swift',
    TEXT_KOTLIN = 'text/kotlin',
    TEXT_SCALA = 'text/scala',
    TEXT_JAVASCRIPT = 'text/javascript',
    TEXT_TYPESCRIPT = 'text/typescript',
    TEXT_HTML = 'text/html',
    TEXT_CSS = 'text/css',
    TEXT_CSV = 'text/csv',
    TEXT_XML = 'text/xml',
    TEXT_YAML = 'text/yaml',
    TEXT_TOML = 'text/toml',
    TEXT_SQL = 'text/sql',
    APPLICATION_JSON = 'application/json',
    APPLICATION_JSONL = 'application/jsonl',
    APPLICATION_PDF = 'application/pdf',
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_SPREADSHEETML_SHEET = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_PRESENTATIONML_PRESENTATION = 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    APPLICATION_MSWORD = 'application/msword',
    APPLICATION_VND_MS_EXCEL = 'application/vnd.ms-excel',
    APPLICATION_VND_MS_POWERPOINT = 'application/vnd.ms-powerpoint',
    APPLICATION_RTF = 'application/rtf',
    APPLICATION_VND_OASIS_OPENDOCUMENT_TEXT = 'application/vnd.oasis.opendocument.text',
}

/**
 * ModelName enum
 */
export enum ModelNameEnum {
    P9_STABLE_STABLE = 'p9-stable-stable',
    P9_LATEST_LATEST = 'p9-latest-latest',
}

/**
 * Role enum
 */
export enum RoleEnum {
    USER = 'user',
    ASSISTANT = 'assistant',
    FUNCTION = 'function',
    SYSTEM = 'system',
}

/**
 * State enum
 */
export enum StateEnum {
    START = 'start',
    QUERY = 'query',
    GENERATING = 'generating',
    ANSWERING = 'answering',
    THINKING = 'thinking',
    PLANNING = 'planning',
    REVIEWING = 'reviewing',
    EXECUTING = 'executing',
    UNDERSTANDING = 'understanding',
    RETRIVING = 'retriving',
    DYNAMIC_RETRIEVAL = 'dynamic_retrieval',
    MSG_UPDATE = 'msg_update',
    GROUNDING = 'grounding',
}

/**
 * UserType enum
 */
export enum UserTypeEnum {
    UI = 'ui',
    USER = 'user',
    ADMIN = 'admin',
    SYSTEM = 'system',
    SERVICE = 'service',
}
