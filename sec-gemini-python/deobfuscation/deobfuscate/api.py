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

import random

from fastmcp import Client
from mcp.types import CallToolResult
from pydantic import BaseModel, ConfigDict


class WebcrackConfig(BaseModel):
    """The configuration used for 'webcrack'."""

    jsx: bool = True
    unpack: bool = True
    unminify: bool = True
    deobfuscate: bool = True
    mangle: bool = False


class AiRenameVariablesConfig(BaseModel):
    """Configuration for variable renaming during a 'deobfuscate' tool call."""

    use_unsafe: bool = False


class DeobfuscateConfig(BaseModel):
    """Configuration to pass to the 'deobfuscate' tool."""

    webcrack_config: WebcrackConfig | bool = WebcrackConfig()
    restringer_config: bool = True
    ai_rename_variables_config: AiRenameVariablesConfig | bool = (
        AiRenameVariablesConfig()
    )

    model_config = ConfigDict(extra="allow")


class ToolError(BaseModel):
    """An error returned from a tool run during 'deobfuscate'."""

    error: str
    tool_name: str

    model_config = ConfigDict()


class McpResult(BaseModel):
    """A common result type used across simple tool calls."""

    result: bytes
    error: str
    mcp_error: str

    model_config = ConfigDict()


class DeobfuscateMcpResult(BaseModel):
    """The result from a 'deobfuscate' tool call."""

    result: bytes
    errors: list[ToolError]
    mcp_error: str

    model_config = ConfigDict()


def _handle_mcp_result(result: CallToolResult) -> McpResult:
    """Handles a FastMCP tool result from an MCP server.

    Args:
      result: The result to handle.
    Returns:
      The MCP result converted to a structured model.
    """
    if result.is_error:
        return McpResult(result="", error="", mcp_error=result["content"]["text"])
    return McpResult(
        result=result.structured_content.get("result"),
        error=result.structured_content.get("error"),
        mcp_error="",
    )


class SecGeminiDeobfuscator:
    """Wraps a FastMCP client that queries the SecGemini deobfuscation API."""

    def __init__(self, api_key: str, mcp_url: str | None = None):
        """Initializes the SecGemini Deobfuscator API client.

        Args:
          api_key: Api key used to authenticate with SecGemini.
          mcp_url: URL of the MCP server to connect to.
        """
        self._client = Client(mcp_url, auth=api_key)

    async def webcrack(
        self, js: str, config: WebcrackConfig = WebcrackConfig()
    ) -> McpResult:
        """Runs the webcrack tool on the MCP server.

        Args:
          js: The Javascript to pass to webcrack.
          config: The configuration used by webcrack.
        """
        session_name = f"webcrack_session_{random.randint(1000, 9999)}"
        if config is None:
            config = WebcrackConfig()
        async with self._client:
            mcp_result = await self._client.call_tool(
                "webcrack",
                {"session_name": session_name, "js": js, "config": config},
                timeout=300000,
            )
            return _handle_mcp_result(mcp_result)

    async def restringer(self, js: str) -> McpResult:
        """Runs the restringer tool on the MCP server.

        Args:
          js: The Javascript to pass to restringer.
        """
        session_name = f"restringer_session_{random.randint(1000, 9999)}"
        async with self._client:
            mcp_result = await self._client.call_tool(
                "restringer", {"session_name": session_name, "js": js}, timeout=300000
            )
            return _handle_mcp_result(mcp_result)

    async def ai_rename_variables(self, js: str, use_unsafe: bool = False) -> McpResult:
        """Runs the AI variable renaming tool on the MCP server.

        Args:
          js: The Javascript to pass to the rename.
          use_unsafe: Whether to rename variables that are in the scope of eval
            statements.
        """
        session_name = f"ai_rename_variables_session_{random.randint(1000, 9999)}"
        async with self._client:
            mcp_result = await self._client.call_tool(
                "ai_rename_variables",
                {"session_name": session_name, "js": js, "use_unsafe": use_unsafe},
                timeout=900000,
            )
            return _handle_mcp_result(mcp_result)

    async def deobfuscate(
        self, js: bytes, config: DeobfuscateConfig = DeobfuscateConfig()
    ) -> DeobfuscateMcpResult:
        """Runs a set of deobfuscation tools on the MCP server.

        Args:
          js: The Javascript to pass to the rename.
          use_unsafe: Whether to rename variables that are in the scope of eval
            statements.
        """
        session_name = f"deobfuscate_session_{random.randint(1000, 9999)}"
        async with self._client:
            mcp_result = await self._client.call_tool(
                "deobfuscate",
                {"session_name": session_name, "js": js, "config": config},
                timeout=900000,
            )
            if mcp_result.is_error:
                return DeobfuscateMcpResult(
                    result="", errors=[], mcp_error=mcp_result["content"]["text"]
                )
            return DeobfuscateMcpResult(
                result=mcp_result.structured_content.get("result"),
                errors=mcp_result.structured_content.get("errors"),
                mcp_error="",
            )
