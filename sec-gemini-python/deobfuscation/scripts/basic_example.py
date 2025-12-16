import asyncio
import os
import sys
from functools import wraps
from pathlib import Path

import dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from deobfuscate import SecGeminiDeobfuscator

dotenv.load_dotenv()

default_mcp_url = os.getenv("DEFAULT_MCP_URL", "").strip()
secgemini_api_key = os.getenv("SEC_GEMINI_API_KEY", "").strip()


def sync(f):
    """Decorator that wraps coroutine with asyncio.run."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@sync
async def main() -> None:
    deobfuscator = SecGeminiDeobfuscator(secgemini_api_key, default_mcp_url)
    print("SecGemini Deobfuscator object instantiated correctly")

    js = "let a = 1;"
    result = await deobfuscator.deobfuscate(js.encode("utf8"))
    print("Full result:")
    print(result)
    print("Result:")
    print(result.result.decode("utf8"))


if __name__ == "__main__":
    main()
