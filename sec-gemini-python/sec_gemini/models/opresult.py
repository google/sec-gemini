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
from typing import Optional

from ..models.enums import ResponseStatus, MimeType


class OpResult(BaseModel):
    ok: bool = Field(
        ...,
        title="Operation Result",
        description="True if the operation was successful.",
    )

    status_code: ResponseStatus = Field(
        ..., title="Status Code", description="HTTP status code to return."
    )

    status_message: str = Field(
        "", title="Error Message", description="Describe why the operation failed."
    )

    data: Optional[dict] = Field(
        None,
        title="Optional data",
        description="Optional field for additional information.",
    )
    mime_type: Optional[MimeType] = Field(
        MimeType.TEXT,
        title="Data Type",
        description="The type of data in the data field.",
    )
    latency: Optional[float] = Field(
        0.0,
        title="Latency",
        description="The time taken to complete the request in seconds.",
    )
