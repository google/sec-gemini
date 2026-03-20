import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sec_gemini import SecGemini

sg = SecGemini()
print("SecGemini object instantiated correctly")

session = sg.create_session()
print("Session created successfully")

resp = session.query(
  'What are the IP addresses of google.com? Reply with this format: {"ips": ["1.2.3.4", ...]}'
)

content = resp.text().strip()
print(f"Raw to the query: {content}")

print("Checking the output... ", end="")
assert re.search(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", content) is not None
print("OK")
