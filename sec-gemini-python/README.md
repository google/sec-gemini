# Sec-Gemini Python SDK

## Installation

```bash
pip install sec_gemini
```

## Basic Usage

```python
from sec_gemini import SecGemini

# initialize the SecGemini SDK
sg = SecGemini()

# create a new session - optionally add a name and description
session = sg.create_session()

# Ask a question
resp = session.query('What are the IP addresses of google.com?')
print(resp.text())
```

