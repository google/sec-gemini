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


class SDKInfo(Enum):
    """SDK Info"""

    NAME = "secgemini-python"
    VERSION = "0.2.0"  # reported in the header of the API


class _URLS(Enum):
    """API URLs"""

    HTTPS = "https://api.secgemini.google"
    WEBSOCKET = "wss://api.secgemini.google"


class _EndPoints(Enum):
    """API Endpoints"""

    # users
    USER_INFO = "/v1/user/info"

    # messages
    GENERATE = "/v1/session/generate"
    STREAM = "/v1/stream"

    # sessions
    REGISTER_SESSION = "/v1/session/register"
    DELETE_SESSION = "/v1/session/delete"
    LIST_SESSION = "/v1/session/list"
    GET_SESSION = "/v1/session/get"
    UPDATE_SESSION = "/v1/session/update"
    SEND_FEEDBACK = "/v1/session/feedback"

    # files
    ATTACH_FILE = "/v1/session/attach_file"
    DELETE_FILE = "/v1/session/delete_file"
