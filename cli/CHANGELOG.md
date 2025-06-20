# Changelog

## 0.0.2-git

### Minor

- Add `sec-gemini --config` to read, write, and delete configuration files
- Add `--shell-{enable,timeout,auto-{exec,read,write}}` for shell command execution (requires `sh`)
- Add interactive commands with `/help` and completion
- Generate interactive session name like the Python SDK
- Use more colors and render markdown
- Add `sec-gemini --completion` to generate shell completion files
- Add icons when bundling packages
- Match recent changes to Sec-Gemini API

### Patch

- Close the web-socket connection when waiting for user input
- Fix panic on malformed server message
- Add sysname and machine to the user agent for HTTP connections
- Add 3 seconds timeout to all HTTP connections to avoid hanging effects
- Improve configuration file handling in case of errors
- Print chain of error causes for failures

## 0.0.1

### Minor

- Add `sec-gemini --check-update` and `--update` to check whether the CLI is up-to-date
- Add `sec-gemini --open-ui` and `--ui` to open the web UI
- Add `--show-thinking` and `SEC_GEMINI_SHOW_THINKING` to print the thinking steps
- Add `--api-key` and `SEC_GEMINI_API_KEY` to bypass configuration file
- Read API key from configuration file and ask interactively the first time
- Add `sec-gemini QUERY...` for single query
- Add `sec-gemini` for interactive session

## 0.0.0

No content.

<!-- Increment to skip CHANGELOG.md test: 4 -->
