# Sec-Gemini swiss-army knife

## For users

### Install

You can download and install binaries from the [latest CLI release][release].

[release]: https://github.com/google/sec-gemini/releases/tag/cli/sec-gemini-v0.0.4

### Usage

The CLI documentation can be accessed from the CLI using `sec-gemini --help`. For example:

```text
% sec-gemini --help
Sec-Gemini swiss-army knife.

Sec-Gemini is an experimental cybersecurity-focused AI from Google. This CLI provides
multiple ways to interact with Sec-Gemini from the command-line.

Usage: sec-gemini [OPTIONS] [QUERY]...
       sec-gemini <COMMAND>

Commands:
  --config               Reads, writes, or deletes configuration files
  --open-ui              Opens the Sec-Gemini web UI in a browser [aliases: --ui]
  --self-update          Updates the CLI if a newer version exists [aliases: --update]
  --generate-completion  Generates a shell completion file [aliases: --completion]

Arguments:
  [QUERY]...
          The query to ask Sec-Gemini (interactive session if omitted).

          If the query is omitted, an interactive session is started where multiple
          queries can be asked successively.

          The query may be split across multiple arguments, in which case they will be
          separated by spaces. The following invocations are equivalent (with common
          shell escaping):

            sec-gemini what is a CVE
            sec-gemini 'what is a CVE'
            sec-gemini   'what is'     a\ CVE

Options:
      --show-thinking[=<SHOW_THINKING>]
          Prints the Sec-Gemini thinking steps

          [env: SEC_GEMINI_SHOW_THINKING=]
          [possible values: true, false]

      --api-key <API_KEY>
          Sec-Gemini API key

          [env: SEC_GEMINI_API_KEY=]

      --local-tool-enable <LOCAL_TOOL_ENABLE>
          Provides Sec-Gemini access to these local tools.

          The format is a space- or comma-separated list of tool prefixes optionally
          preceded by an exclamation mark (to disable instead of enable). The list is
          evaluated from the first prefix in order until the last prefix. Initially, all
          tools are assumed enabled.

          For example, the empty string enables all tools, an exclamation mark disables
          all tools, !,file,!file_write would only enable file tools (like file_read or file_sha256)
          that are not file_write, and !net net_tcp would disable network tools except net_tcp
          ones.

          [env: SEC_GEMINI_LOCAL_TOOL_ENABLE=]

      --local-tool-ask-before <LOCAL_TOOL_ASK_BEFORE>
          When to ask before executing a local tool

          [env: SEC_GEMINI_LOCAL_TOOL_ASK_BEFORE=]
          [possible values: never, destructive, mutating, always]

      --local-tool-ask-after <LOCAL_TOOL_ASK_AFTER>
          Whether to ask for sending the response after executing a local tool

          [env: SEC_GEMINI_LOCAL_TOOL_ASK_AFTER=]
          [possible values: true, false]

      --local-tool-timeout <LOCAL_TOOL_TIMEOUT>
          How long a local tool can run before sending the output to Sec-Gemini

          [env: SEC_GEMINI_LOCAL_TOOL_TIMEOUT=]

      --local-tool-idle-time <LOCAL_TOOL_IDLE_TIME>
          How long a local tool can idle before sending the output to Sec-Gemini

          [env: SEC_GEMINI_LOCAL_TOOL_IDLE_TIME=]

  -h, --help
          Print help (see a summary with '-h')

  -V, --version
          Print version
```

Suffixing `--help` to a command line will print the documentation relevant for that command line.
For example, the documentation of the `--ui` command can be accessed like that:

```text
% sec-gemini --open-ui --help
Opens the Sec-Gemini web UI in a browser

Usage: sec-gemini --open-ui

Options:
  -h, --help  Print help
```

## For developers

### Build

You need `cargo` to compile the CLI. The simplest solution is to install `rustup` according to
<https://rustup.rs/>, but installing `cargo` from your distribution (e.g. `apt install cargo`)
should work too.

You can compile the CLI with:

```shell
cargo build --release
```

The binary is written to `./target/release/sec-gemini`.

### Install

You can install the CLI with:

```shell
cargo install --path=.
```

### Test

You need `rustup` with both the `stable` and the `nightly` toolchains installed. The `nightly`
toolchain must be the default.

You can run the unit tests with:

```shell
./test.sh
```

Besides the `rustup` requirements for the unit tests, you need `taplo` to run the continuous
integration. You can install it with:

```shell
cargo install taplo-cli
```

You can run the continuous integration with:

```shell
./ci.sh
```

### Release

You can create a release commit with:

```shell
./release.sh
```

Once the commit is merged to the `main` branch, you can trigger the CLI workflow to create the
release and associated tag.
