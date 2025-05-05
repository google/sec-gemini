
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

class ModelSubAgentInfo(BaseModel):
    """Describes the components of a Sec-Gemini model."""
    name: str = Field(..., title="Component Name", description="The name of the component.")
    version: int = Field(..., title="Component Version", description="The version of the component.")
    description: Optional[str] = Field(None, title="Component Description", description="A brief description of the component.")
    vendor: str = Field(..., title="Component Vendor", description="The vendor of the component.")
    is_enabled: bool = Field(True, title="Is Enabled", description="Whether the component is enabled or not.")
    is_optional: bool = Field(False, title="Is Optional", description="Whether the component is optional or not.")
    is_experimental: bool = Field(False, title="Is Experimental", description="Whether the component is experimental or not.")

class ModelInfo(BaseModel):
    """Describes a Sec-Gemini model."""
    model_string: str = Field(..., title="Model String", description="The string used to identify the model.")
    version: str = Field(..., title="Model Version", description="The version of the model.")
    is_experimental: bool = Field(False, title="Is Experimental", description="Whether the model is experimental or not.")
    subagents: list[ModelSubAgentInfo] = Field([], title="Subagents", description="The list of subagents that make up the model.")