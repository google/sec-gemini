import json
import re

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

info = json.loads(content)
assert "ips" in info.keys()
assert len(info["ips"]) > 0
for ip in info["ips"]:
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", ip)
print("Answer passed all checks.")
