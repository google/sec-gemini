import base64
import os
import sys

import dotenv
import httpx
from openai import OpenAI

dotenv.load_dotenv()

TEST_PDF_URL = "https://elie.net/static/files/retsim-resilient-and-efficient-text-similarity/retsim-resilient-and-efficient-text-similarity.pdf"

api_key = os.getenv("SEC_GEMINI_API_KEY", "").strip()
if api_key == "":
  print(
    "ERROR: this example requires a valid api key in the SEC_GEMINI_API_KEY env variable"
  )
  sys.exit(1)

base_url = os.getenv("SEC_GEMINI_API_HTTP_URL", "https://api.secgemini.google")

print(f'Connecting to "{base_url}"')

client = OpenAI(
  base_url=base_url,
  api_key=api_key,
  max_retries=1,
)


filename = TEST_PDF_URL.split("/")[-1]

res = httpx.get(TEST_PDF_URL)
assert res.status_code == 200
b64_file_content = base64.b64encode(res.content).decode("ascii")


response = client.chat.completions.create(
  model="sec-gemini-1.1",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": (
            "The file in attachment should be about a tool in machine learning. What is the name of the tool?"
            "Just output one word, nothing else."
          ),
        },
        {
          "type": "file",
          "file": {
            "filename": filename,
            "file_data": f"data:application/pdf;base64,{b64_file_content}",
          },
        },
      ],
    }
  ],
)

print(f"Raw response {response}")

print("Checking the output... ", end="")
assert response.choices[0].message.content is not None
assert response.choices[0].message.content.lower().find("retsim") >= 0
print("OK")
