# Changelog

## 0.0.2-git

### Minor

- Add `sec-gemini --config` to read, write, and delete configuration files
- Add shell command execution (requires `sh`)
- Add interactive commands with help and completion
- Generate interactive session name like the Python SDK
- Add markdown rendering support
- Use more colors in interactive session
- Add `sec-gemini --completion` to generate shell completion files
- Add icons when bundling packages
- Improve configuration file handling in case of errors
- Print chain of error causes for failures
- Match recent changes to Sec-Gemini API

### Patch

- Add 3 seconds timeout to all HTTP connections to avoid hanging effects

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

<!-- Increment to skip CHANGELOG.md test: 2 -->
