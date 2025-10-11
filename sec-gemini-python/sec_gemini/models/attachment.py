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


from typing import Optional

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Represents a file upload to the session."""

    session_id: str = Field(
        ...,
        title="Session ID",
        description="The session ID this file should be attached to.",
    )

    filename: str = Field(
        ...,
        title="Filename",
        description="The name of the file.",
    )

    mime_type: Optional[str] = Field(
        None,
        title="Mime Type",
        description="The mime type of the file. This is used as a hint, and it may be overridden.",
        deprecated=True,
    )

    content: str = Field(
        ...,
        title="File Content",
        description="The content of the file as string. Always base64 encoded.",
    )
