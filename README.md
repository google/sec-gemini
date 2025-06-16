# Sec-Gemini SDKs

This repository hosts SDKs for Sec-Gemini, an experimental cybersecurity-focused AI from Google.

SDKs are available for:

* Python in `sec-gemini-python/`
* TypeScript `sec-gemini-ts/`


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

For more information on Sec-Gemini, visit [https://secgemini.google](https://secgemini.google).




This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
