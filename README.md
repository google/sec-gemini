# Sec-Gemini SDKs and CLI

This repository hosts SDKs and a CLI for Sec-Gemini, an experimental cybersecurity-focused AI from
Google.

## SDKs

SDKs are available for:

* Python in `sec-gemini-python/`
* TypeScript in `sec-gemini-ts/`

We also have a web component to ease integration on your website. Here's how to load it:

```html
<sec-gem-chat
      incognito="true"
      session-id=""
      session-name="TestName"
      session-description="TestDescription"
      session-prompt=""
      theme="dark"
      api-key="..."
    >
    </sec-gem-chat>
<script src='https://cdn.jsdelivr.net/npm/sec-gemini-web-component/dist/swc.iife.js'>
```

## CLI

The CLI can be installed on Linux and macOS:

```shell
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/google/sec-gemini/releases/download/cli/sec-gemini-v0.0.3/sec-gemini-installer.sh | sh
```

And for Windows:

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://github.com/google/sec-gemini/releases/download/cli/sec-gemini-v0.0.3/sec-gemini-installer.ps1 | iex"
```

## Website

For more information on Sec-Gemini, visit [https://secgemini.google](https://secgemini.google).

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
