
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


"Definition used to allows clients to pass local tools to the orchestrator."
import json # noqa: E402
from enum import Enum # noqa: E402
from pydantic import BaseModel, Field, field_validator # noqa: E402
from typing import List, Dict, Any, Optional, Union # noqa: E402


class Type(str, Enum):
    """Optional. The type of the field."""

    TYPE_UNSPECIFIED = "type_unspecified"  # "not specified, should not be used"
    STRING = "string"  # "string type"
    NUMBER = "number"  # "number type"
    INTEGER = "integer"  # "integer type"
    BOOLEAN = "boolean"  # "boolean type"
    ARRAY = "array"  # "array type"
    OBJECT = "object"  # "object type"
    NULL = "null"  # "null type"


class Schema(BaseModel):
    """Schema is used to define the format of input/output data.

    Represents a select subset of an [OpenAPI 3.0 schema
    object](https://spec.openapis.org/oas/v3.0.3#schema-object). More fields may
    be added in the future as needed.
    """

    additional_properties: Optional[Any] = Field(
        default=None,
        description="""Optional. Can either be a boolean or an object; controls the presence of additional properties.""",
    )
    defs: Optional[dict[str, "Schema"]] = Field(
        default=None,
        description="""Optional. A map of definitions for use by `ref` Only allowed at the root of the schema.""",
    )
    ref: Optional[str] = Field(
        default=None,
        description="""Optional. Allows indirect references between schema nodes. The value should be a valid reference to a child of the root `defs`. For example, the following schema defines a reference to a schema node named "Pet": type: object properties: pet: ref: #/defs/Pet defs: Pet: type: object properties: name: type: string The value of the "pet" property is a reference to the schema node named "Pet". See details in https://json-schema.org/understanding-json-schema/structuring""",
    )
    any_of: Optional[list["Schema"]] = Field(
        default=None,
        description="""Optional. The value should be validated against any (one or more) of the subschemas in the list.""",
    )
    default: Optional[Any] = Field(default=None, description="""Optional. Default value of the data.""")
    description: Optional[str] = Field(default=None, description="""Optional. The description of the data.""")
    enum: Optional[list[str]] = Field(
        default=None,
        description="""Optional. Possible values of the element of primitive type with enum format. Examples: 1. We can define direction as : {type:STRING, format:enum, enum:["EAST", NORTH", "SOUTH", "WEST"]} 2. We can define apartment number as : {type:INTEGER, format:enum, enum:["101", "201", "301"]}""",
    )
    example: Optional[Any] = Field(
        default=None,
        description="""Optional. Example of the object. Will only populated when the object is the root.""",
    )
    format: Optional[str] = Field(
        default=None,
        description="""Optional. The format of the data. Supported formats: for NUMBER type: "float", "double" for INTEGER type: "int32", "int64" for STRING type: "email", "byte", etc""",
    )
    items: Optional["Schema"] = Field(
        default=None,
        description="""Optional. SCHEMA FIELDS FOR TYPE ARRAY Schema of the elements of Type.ARRAY.""",
    )
    max_items: Optional[int] = Field(
        default=None,
        description="""Optional. Maximum number of the elements for Type.ARRAY.""",
    )
    max_length: Optional[int] = Field(
        default=None,
        description="""Optional. Maximum length of the Type.STRING""",
    )
    max_properties: Optional[int] = Field(
        default=None,
        description="""Optional. Maximum number of the properties for Type.OBJECT.""",
    )
    maximum: Optional[float] = Field(
        default=None,
        description="""Optional. Maximum value of the Type.INTEGER and Type.NUMBER""",
    )
    min_items: Optional[int] = Field(
        default=None,
        description="""Optional. Minimum number of the elements for Type.ARRAY.""",
    )
    min_length: Optional[int] = Field(
        default=None,
        description="""Optional. SCHEMA FIELDS FOR TYPE STRING Minimum length of the Type.STRING""",
    )
    min_properties: Optional[int] = Field(
        default=None,
        description="""Optional. Minimum number of the properties for Type.OBJECT.""",
    )
    minimum: Optional[float] = Field(
        default=None,
        description="""Optional. SCHEMA FIELDS FOR TYPE INTEGER and NUMBER Minimum value of the Type.INTEGER and Type.NUMBER""",
    )
    nullable: Optional[bool] = Field(
        default=None,
        description="""Optional. Indicates if the value may be null.""",
    )
    pattern: Optional[str] = Field(
        default=None,
        description="""Optional. Pattern of the Type.STRING to restrict a string to a regular expression.""",
    )
    properties: Optional[dict[str, "Schema"]] = Field(
        default=None,
        description="""Optional. SCHEMA FIELDS FOR TYPE OBJECT Properties of Type.OBJECT.""",
    )
    property_ordering: Optional[list[str]] = Field(
        default=None,
        description="""Optional. The order of the properties. Not a standard field in open api spec. Only used to support the order of the properties.""",
    )
    required: Optional[list[str]] = Field(
        default=None,
        description="""Optional. Required properties of Type.OBJECT.""",
    )
    title: Optional[str] = Field(default=None, description="""Optional. The title of the Schema.""")
    type: Optional[Type] = Field(default=None, description="""Optional. The type of the data.""")

    @field_validator("type", mode="before")
    @classmethod
    def validate_type_case_insensitive(cls, v: Any) -> str:
        if isinstance(v, str):
            # Try to match case-insensitively
            for type_enum in Type:
                if v.lower() == type_enum.value.lower():
                    return type_enum.value
        return v


class LocalTool(BaseModel):
    """
    Normalized representation of a tool/function.
    """

    name: str = Field(..., description="The unique name/identifier of the tool", min_length=1)
    description: str = Field(..., description="Comprehensive description of what the tool does", min_length=1)
    parameters: Schema = Field(..., description="Schema defining the input parameters")

    returns: Optional[Schema] = Field(None, description="Schema defining the output/return value")
    version: Optional[str] = Field(None, description="Version identifier for this tool definition")
    tags: Optional[List[str]] = Field(None, description="List of tags for categorization")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocalTool":
        """
        Creates a Tool instance from a dictionary.

        This method normalizes input from different formats (e.g., MCP)
        by renaming keys like 'inputSchema' to the model's internal 'parameters'
        field before validation. It does not modify the original input dictionary.
        """
        # Create a shallow copy to avoid modifying the caller's original dictionary
        normalized_data = data.copy()

        if "inputSchema" in normalized_data:
            normalized_data["parameters"] = normalized_data.pop("inputSchema")
        if "outputSchema" in normalized_data:
            normalized_data["returns"] = normalized_data.pop("outputSchema")

        # Validate the normalized data
        return cls.model_validate(normalized_data)

    @classmethod
    def from_json(cls, data: str) -> "LocalTool":
        """
        Creates a Tool instance from a JSON string.
        """
        dict_data = json.loads(data)
        return cls.from_dict(dict_data)

    def to_json(self) -> str:
        """Converts the Tool to json function calling format."""
        data = self.model_dump_json(exclude_none=True)
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Tool to a dictionary."""
        return self.model_dump(exclude_none=True)

    def to_mcp(self) -> str:
        """Converts the Tool to MCP (Model Context Protocol) format."""
        data = self.model_dump(exclude_none=True)
        # Rename keys to match MCP format
        if "parameters" in data:
            data["inputSchema"] = data.pop("parameters")
        if "returns" in data:
            data["outputSchema"] = data.pop("returns")
        return json.dumps(data)
