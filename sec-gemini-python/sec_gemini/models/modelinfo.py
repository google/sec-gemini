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


class ToolSetVendor(BaseModel):
    """Vendor Toolsets info."""

    name: str = Field(
        ...,
        title="Vendor Name",
        description="The name of the vendor providing the tool or agent.",
    )

    description: str = Field(
        ...,
        title="Vendor Description",
        description="A brief description of the vendor.",
    )

    url: str = Field(..., title="Vendor URL", description="The URL of vendor.")

    svg: str = Field(
        ..., title="Vendor SVG Icon", description="The SVG icon of the vendor."
    )


class OptionalToolSet(BaseModel):
    """Describes the toolsets of a Sec-Gemini model."""

    name: str = Field(..., title="toolset Name", description="The name of the toolset.")
    version: int = Field(
        ..., title="toolset Version", description="The version of the toolset."
    )
    description: Optional[str] = Field(
        None,
        title="toolset Description",
        description="A brief description of the toolset.",
    )
    vendor: ToolSetVendor = Field(
        ..., title="toolset Vendor", description="The vendor of the toolset."
    )

    is_enabled: bool = Field(
        True, title="Is Enabled", description="Whether the toolset is enabled or not."
    )
    is_experimental: bool = Field(
        False,
        title="Is Experimental",
        description="Whether the toolset is experimental or not.",
    )


class ModelInfo(BaseModel):
    """Describes a Sec-Gemini model."""

    model_string: str = Field(
        ..., title="Model String", description="The string used to identify the model."
    )
    version: str = Field(
        ..., title="Model Version", description="The version of the model."
    )
    is_experimental: bool = Field(
        False,
        title="Is Experimental",
        description="Whether the model is experimental or not.",
    )
    toolsets: list[OptionalToolSet] = Field(
        [], title="Tools", description="Toggable tools used by the model."
    )
