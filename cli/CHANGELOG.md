# Changelog

## 0.0.5-git

### Major

- Remove all shell related functionalities (replaced by the shell local tool)

### Minor

- Add `--local-tool-enable` to select which local tools to enable
- Add `--local-tool-ask-before` to select which local tools need confirmation (can be `never` to
  never ask, `destructive` to only ask for destructive tools, `mutating` to always ask except for
  read-only tools, and `always` to always ask)
- Add `--local-tool-ask-after` to configure whether confirmation is needed to send tool responses
- Add `--local-tool-timeout` to configure the maximum time to wait for a tool output
- Add `--local-tool-idle-time` to configure the maximum time to wait for a tool output after the
  last output
- Add `/config list` to list the local tools enabled in the current session
- Add `/config list --available=true` to list the available local tools
- Ensure cached credentials for sudo in a separate step

### Patch

- Support the new internal message timestamp logic
- Fix bug where commands don't have time to terminate

## 0.0.4

### Minor

- Add `/shell` command to simulate a Sec-Gemini request
- Add visible confirmation after multi-line query
- Don't print the user and org id anymore
- Add `/session list --debug` argument
- Support complex markdown heading

### Patch

- Fix wrapping behavior for input query
- Fix shell command output being partially discarded on command exit
- Fix deadlock with single queries creating the query session

## 0.0.3

### Major

- Rename `--check-update` to `--self-update` and perform the update

### Minor

- Add `shell-idle-time` to avoid waiting the full `shell-timeout`
- Match recent changes to Sec-Gemini API

### Patch

- Fix the environment variable of `shell-timeout`
- Disable `shell-timeout` and `shell-idle-time` for sudo commands
- Consider error messages as recoverable
- Reconnect to the session if closed while sending
- Handle closed web-socket without failing

## 0.0.2

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

<!-- Increment to skip CHANGELOG.md test: 6 -->
