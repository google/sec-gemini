# Sec-Gemini swiss-army knife

## For users

Pre-built binaries will eventually be released on GitHub. In the meantime, you can build the binary
following the documentation for developers below.

The CLI documentation can be accessed from the CLI using `sec-gemini help`. For example:

```shell
% sec-gemini help
Sec-Gemini swiss-army knife

Usage: sec-gemini [OPTIONS] <COMMAND>

Commands:
  query    Sends a single query to Sec-Gemini and prints the result
  session  Opens an interactive session with Sec-Gemini in the terminal
  web-ui   Opens the Sec-Gemini web UI in a browser
  help     Print this message or the help of the given subcommand(s)

Options:
      --api-key <API_KEY>  Sec-Gemini API key [env: SEC_GEMINI_API_KEY=p9811F-O1EB-XEB3-JOI6-P1UD]
      --execution-flow     Prints the execution flow [env: SEC_GEMINI_EXECUTION_FLOW=]
  -h, --help               Print help
  -V, --version            Print version
```

```shell
% sec-gemini help query
Sends a single query to Sec-Gemini and prints the result

Usage: sec-gemini query [PROMPT]...

Arguments:
  [PROMPT]...
          The prompt of the query.

          You can use multiple arguments, in which case they will be separated by spaces. The
          following invocations are equivalent (with common shell escaping):

              sec-gemini query 'what is a CVE'
              sec-gemini query what is a CVE
              sec-gemini query   'what is'     a\ CVE

Options:
  -h, --help
          Print help (see a summary with '-h')
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

### Unit tests

You can run the unit tests with:

```shell
./test.sh
```

### Continuous integration

You need `taplo` to run the continuous integration. You can install it with:

```shell
cargo install taplo-cli
```

You can run the continuous integration with:

```shell
./ci.sh
```
