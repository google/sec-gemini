# Sec-Gemini swiss-army knife

## For users

Pre-built binaries will eventually be released on GitHub. In the meantime, you can build the binary
following the documentation for developers below.

The CLI documentation can be accessed from the CLI using `sec-gemini help`. For example:

```shell
% sec-gemini help
Sec-Gemini swiss-army knife.

Usage: sec-gemini <COMMAND>

Commands:
  query  Sends a single query to Sec-Gemini
  help   Print this message or the help of the given subcommand(s)

Options:
  -h, --help     Print help
  -V, --version  Print version
```

```shell
% sec-gemini help query
Sends a single query to Sec-Gemini

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
