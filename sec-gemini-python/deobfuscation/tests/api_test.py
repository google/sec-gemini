import pytest
from fastmcp import Client, FastMCP
from fastmcp.client import BearerAuth, FastMCPTransport

from deobfuscate import (
    DeobfuscateConfig,
    DeobfuscateMcpResult,
    McpResult,
    SecGeminiDeobfuscator,
    ToolError,
    WebcrackConfig,
)


@pytest.fixture
def fastmcp_server():
    """Fixture that creates a FastMCP server with tools."""
    server = FastMCP("TestDeobfuscationServer")

    @server.tool
    def webcrack(
        session_name: str, js: bytes, config: WebcrackConfig | None = WebcrackConfig()
    ):
        """Runs webcrack against the given Javascript."""
        if js == b"bad code":
            return {"result": "", "error": "failure"}
        return {"result": "Deobfuscated code", "error": ""}

    @server.tool
    def restringer(session_name: str, js: bytes):
        """Runs restringer against the given Javascript."""
        if js == b"bad code":
            return {"result": "", "error": "failure"}
        return {"result": "Deobfuscated code", "error": ""}

    @server.tool
    def ai_rename_variables(session_name: str, js: bytes, use_unsafe: bool):
        """Renames variables in the given Javascript."""
        if js == b"bad code":
            return {"result": "", "error": "failure"}
        return {"result": f"Deobfuscated code, unsafe: {use_unsafe}", "error": ""}

    @server.tool
    def deobfuscate(
        session_name: str,
        js: bytes,
        config: DeobfuscateConfig | None = DeobfuscateConfig(),
    ):
        """Deobfuscates the given Javascript."""
        if js == b"bad code":
            return {
                "result": "",
                "errors": [{"tool_name": "webcrack", "error": "failure"}],
            }
        return {"result": "Deobfuscated code", "errors": []}

    return server


def create_deobfuscator(fastmcp_server):
    deobfuscator = SecGeminiDeobfuscator("123", "http://localhost:8000")
    # Resetting the client so that we can use our mock server. The transport should only be checked in the deobfuscator client creation test.
    deobfuscator._client = Client(transport=FastMCPTransport(fastmcp_server))
    return deobfuscator


async def test_deobfuscator_creation():
    """Test creating a SecGeminiDeobfuscator client."""
    deobfuscator = SecGeminiDeobfuscator("123", "http://localhost:8000")
    assert isinstance(deobfuscator._client.transport.auth, BearerAuth)
    assert deobfuscator._client.transport.auth.token.get_secret_value() == "123"


###############################################################################
# 'deobfuscate' tests
###############################################################################


async def test_successfully_deobfuscate_without_config(fastmcp_server):
    """Test deobfuscating using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.deobfuscate("console.log(1)")

    assert result == DeobfuscateMcpResult(
        result="Deobfuscated code", errors=[], mcp_error=""
    )


async def test_successfully_deobfuscate_with_config(fastmcp_server):
    """Test deobfuscating using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.deobfuscate("console.log(1)", DeobfuscateConfig())

    assert result == DeobfuscateMcpResult(
        result="Deobfuscated code", errors=[], mcp_error=""
    )


async def test_fail_to_deobfuscate(fastmcp_server):
    """Test deobfuscating using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.deobfuscate("bad code", DeobfuscateConfig())

    assert result == DeobfuscateMcpResult(
        result="",
        errors=[ToolError(tool_name="webcrack", error="failure")],
        mcp_error="",
    )
    assert isinstance(result, DeobfuscateMcpResult)


###############################################################################
# 'webcrack' tests
###############################################################################


async def test_successfully_run_webcrack_without_config(fastmcp_server):
    """Test running webcrack using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.webcrack("console.log(1)")

    assert result == McpResult(result="Deobfuscated code", error="", mcp_error="")


async def test_successfully_run_webcrack_with_config(fastmcp_server):
    """Test running webcrack using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.webcrack("console.log(1)", WebcrackConfig())

    assert result == McpResult(result="Deobfuscated code", error="", mcp_error="")


async def test_fail_to_run_webcrack(fastmcp_server):
    """Test running webcrack using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.webcrack("bad code", WebcrackConfig())

    assert result == McpResult(result="", error="failure", mcp_error="")
    assert isinstance(result, McpResult)


###############################################################################
# 'restringer' tests
###############################################################################


async def test_successfully_run_restringer(fastmcp_server):
    """Test running restringer using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.restringer("console.log(1)")

    assert result == McpResult(result="Deobfuscated code", error="", mcp_error="")


async def test_fail_to_run_restringer(fastmcp_server):
    """Test running restringer using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.restringer("bad code")

    assert result == McpResult(result="", error="failure", mcp_error="")
    assert isinstance(result, McpResult)


###############################################################################
# 'ai_rename_variables' tests
###############################################################################


async def test_successfully_rename_variables(fastmcp_server):
    """Test renaming variables using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.ai_rename_variables("console.log(1)")

    assert result == McpResult(
        result="Deobfuscated code, unsafe: False", error="", mcp_error=""
    )


async def test_successfully_unsafe_rename_variables(fastmcp_server):
    """Test renaming variables using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.ai_rename_variables("console.log(1)", use_unsafe=True)

    assert result == McpResult(
        result="Deobfuscated code, unsafe: True", error="", mcp_error=""
    )


async def test_fail_to_rename_variables(fastmcp_server):
    """Test renaming variables using the SecGeminiDeobfuscator client."""
    deobfuscator = create_deobfuscator(fastmcp_server)
    result = await deobfuscator.ai_rename_variables("bad code")

    assert result == McpResult(result="", error="failure", mcp_error="")
    assert isinstance(result, McpResult)
