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

class KeyInfo(BaseModel):
    """
    Represents a key that can be uploaded to the API.
    """

    key: str = Field(
        ...,
        title="API Key",
        description="The API key content."
    )

    rpm: int = Field(...,
                     title="Request Per Minute (RPM)",
                     description="The number of requests allowed per minute.")

    tpm: int = Field(...,
                     title="Token Per Minute (TPM)",
                     description="The number of tokens allowed per minute.")

    is_admin: bool = Field(...,
                           title="Is Admin",
                           description="Whether the key is an admin key.")

    is_logging: bool = Field(...,
                             title="Is Logging",
                             description="Whether user data associated with the key is logged.")
