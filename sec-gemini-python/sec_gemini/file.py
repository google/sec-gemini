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

from pydantic import BaseModel, Field
from .models.enums import MimeType


class File(BaseModel):
    """
    Represents a file that can be uploaded to the API.
    """

    filename: str = Field(..., title="Filename", description="The name of the file.")

    mime_type: MimeType = Field(
        ..., title="Mime Type", description="The mime type of the file."
    )

    file: bytes = Field(..., title="File", description="The file content.")
