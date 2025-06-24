# Sec-Gemini swiss-army knife

## For users

### Install

You can download and install binaries from the [latest CLI release][release].

[release]: https://github.com/google/sec-gemini/releases/tag/cli/sec-gemini-v0.0.3

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

      --shell-enable <SHELL_ENABLE>
          Whether Sec-Gemini can ask to execute shell commands

          [env: SEC_GEMINI_SHELL_ENABLE=]
          [possible values: auto, false, true]

      --shell-timeout <SHELL_TIMEOUT>
          How long a shell command can run before sending the output to Sec-Gemini

          [env: SEC_GEMINI_SHELL_TIMEOUT=]

      --shell-idle-time <SHELL_IDLE_TIME>
          How long a shell command can idle before sending the output to Sec-Gemini

          [env: SEC_GEMINI_SHELL_IDLE_TIME=]

      --shell-auto-exec <SHELL_AUTO_EXEC>
          Whether Sec-Gemini can execute shell commands without confirmation

          [env: SEC_GEMINI_SHELL_AUTO_EXEC=]
          [possible values: true, false]

      --shell-auto-read <SHELL_AUTO_READ>
          Whether Sec-Gemini can read the result of shell commands without confirmation

          [env: SEC_GEMINI_SHELL_AUTO_READ=]
          [possible values: true, false]

      --shell-auto-write <SHELL_AUTO_WRITE>
          Whether Sec-Gemini can write input to shell commands without confirmation

          [env: SEC_GEMINI_SHELL_AUTO_WRITE=]
          [possible values: true, false]

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
