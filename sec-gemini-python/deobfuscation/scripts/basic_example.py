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
