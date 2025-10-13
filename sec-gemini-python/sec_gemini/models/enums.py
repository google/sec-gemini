# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from enum import Enum


class FeedbackType(str, Enum):
    """Type of feedback that can be sent to the system."""

    USER_FEEDBACK = "user_feedback"
    BUG_REPORT = "bug_report"


class VectorDistance(str, Enum):
    COSINE = "COSINE"
    DOT_PRODUCT = "DOT_PRODUCT"
    EUCLIDEAN = "EUCLIDEAN"


class UserType(str, Enum):
    "User type"

    UI = "ui"  # user interface
    USER = "user"  # system user
    ADMIN = "admin"  # admin user
    SYSTEM = "system"  # orchestrator system user
    SERVICE = "service"  # microservice


class ResponseStatus(int, Enum):
    # 2xx Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206

    # 3xx Redirection
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    # 4xx Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    AUTHENTICATION_ERROR = 401  # Alias for UNAUTHORIZED
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    ALREADY_EXISTS = 409  # Alias for CONFLICT
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    I_AM_A_TEAPOT = 418
    UNPROCESSABLE_ENTITY = 422
    TOO_EARLY = 425
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    QUOTA_EXCEEDED = 429  # Alias for TOO_MANY_REQUESTS
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    UNAVAILABLE_FOR_LEGAL_REASONS = 451

    # 5xx Server Errors
    INTERNAL_SERVER_ERROR = 500
    SERVER_ERROR = 500  # Alias for INTERNAL_SERVER_ERROR
    INTERNAL_ERROR = 500  # Another alias for INTERNAL_SERVER_ERROR
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511


class Role(str, Enum):
    "Describe the role associated with the completion"

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"  # those are not returned to the user


class MimeType(str, Enum):
    "Completion type"

    TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    SERIALIZED_JSON = "text/serialized-json"
    BINARY = "application/octet-stream"

    # IMAGES
    JPEG = "image/jpeg"
    PNG = "image/png"
    TIFF = "image/tiff"
    GIF = "image/gif"
    SVG = "image/svg+xml"
    WEBP = "image/webp"
    AVIF = "image/avif"

    # AUDIO
    WAV = "audio/wav"
    MP3 = "audio/mpeg"
    OGG = "audio/ogg"

    # VIDEO
    WEBM = "video/webm"
    MP4 = "video/mp4"

    # CODE
    C = "text/c"
    CPP = "text/c++"
    JAVA = "text/java"
    RUST = "text/rust"
    GOLANG = "text/go"
    PYTHON = "text/python"
    PHP = "text/php"
    PERL = "text/perl"
    RUBY = "text/ruby"
    SWIFT = "text/swift"
    KOTLIN = "text/kotlin"
    SCALA = "text/scala"
    JAVASCRIPT = "text/javascript"
    TYPESCRIPT = "text/typescript"
    HTML = "text/html"
    CSS = "text/css"

    # DATA
    CSV = "text/csv"
    XML = "text/xml"
    YAML = "text/yaml"
    TOML = "text/toml"
    SQL = "text/sql"
    JSON = "application/json"
    JSONL = "application/jsonl"

    # COMPRESSED
    # NOTE: Gemini does not support compressed files
    # ZIP = "application/zip"
    # TAR = "application/tar"
    # GZIP = "application/gzip"
    # BZIP2 = "application/bzip2"
    # XZ = "application/xz"
    # SEVENZIP = "application/x-7z-compressed"

    # DOCUMENTS
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    DOC = "application/msword"
    XLS = "application/vnd.ms-excel"
    PPT = "application/vnd.ms-powerpoint"
    RTF = "application/rtf"
    ODT = "application/vnd.oasis.opendocument.text"

    # Internal types used by the orchestrator to control the UI display
    SG_GRAPH = "sec-gemini/graph"  # internal type used to represent a graph
    SG_TIMELINE = "sec-gemini/timeline"  # internal type used to represent a timeline
    SG_TABLE = "sec-gemini/table"  # internal type used to represent a table
    SG_IMAGE = "sec-gemini/image"  # internal type used to represent an image / base64.
    SG_CODE = "sec-gemini/code"  # internal type used to represent a code generation / execution block
    SG_MARKDOWN = (
        "sec-gemini/markdown"  # internal type used to represent a markdown block
    )
    SG_JSON = "sec-gemini/json"  # internal type used to represent a json block
    SG_HTML = "sec-gemini/html"  # internal type used to represent an html block
    SG_CANVAS = "sec-gemini/canvas"  # internal type used to represent a canvas block


class State(str, Enum):
    UNDEFINED = "undefined"

    START = "start"  # turn started
    END = "end"  # turn completed

    QUERY = "query"  # user query

    RUNNING_AGENT = "running_agent"  # executing agent
    AGENT_DONE = "agent_done"  # agent done

    CODING = "coding"  # executing code
    CODE_RESULT = "code_result"  # code result

    CALLING_TOOL = "calling_tool"  # executing function
    TOOL_RESULT = "tool_result"  # function result

    # semantic sugar states
    GENERATING = "generating"  # generating response
    ANSWERING = "answering"  # generating answer
    THINKING = "thinking"  # thinking
    PLANNING = "planning"  # planning execution
    REVIEWING = "reviewing"  # reviewing current result
    UNDERSTANDING = "understanding"  # intent detection
    RETRIEVING = "retrieving"  # retrieving info
    GROUNDING = "grounding"  # grounding


class MessageType(str, Enum):
    "Type of message"

    # info messages
    RESULT = "result"  # result message
    SOURCE = "source"  # cite a source used during the generation
    DEBUG = "debug"  # debug message
    INFO = "info"  # transient info message only used in streaming
    ERROR = "error"  # error message
    THINKING = "thinking"  # thinking message that persist in the thinking panel

    # mutation messages
    UPDATE = (
        "update"  # update message that modify the output. e.g grounding or new fact
    )
    DELETE = "delete"  # Ask to delete a previous message by id

    # User actions
    CONFIRMATION_REQUEST = "confirmation_request"  # Ask for confirmation
    CONFIRMATION_RESPONSE = "confirmation_response"  # Confirmation response

    # User messages
    QUERY = "query"

    # Local tool messages
    LOCAL_TOOL_CALL = "local_tool_call"
    LOCAL_TOOL_RESULT = "local_tool_result"
