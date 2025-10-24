import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sec_gemini import SecGemini


async def main():
  print("Creating secgemini")
  sg = SecGemini()
  session = sg.create_session()
  print("OK")
  prompt = (
    "This is a test prompt, just reply with a random number from 1 to 10!"
  )

  async for message in session.stream(prompt):
    print(message)


if __name__ == "__main__":
  asyncio.run(main())
