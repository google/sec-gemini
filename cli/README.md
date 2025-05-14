# Sec-Gemini swiss-army knife

## For users

### Install

You can download binaries and packages from the [latest CLI release][release] and install them
accordingly. For example:

```shell
# For the Debian package.
sudo dpkg -i sec-gemini.deb

# For the Linux binary.
chmod +x sec-gemini_x86_64-unknown-linux-gnu
mv sec-gemini_x86_64-unknown-linux-gnu "${PATH%%:*}"/sec-gemini
```

If a binary is missing for your platform, if a package is missing for your distribution, or if you
face any issue installing a package or running a binary, please search the existing [issues][issues]
for an existing one to upvote or create a new one otherwise.

[issues]: https://github.com/google/sec-gemini/issues
[release]: https://github.com/google/sec-gemini/releases/tag/cli/v0.0.1

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
  --open-ui       Opens the Sec-Gemini web UI in a browser [aliases: --ui]
  --check-update  Checks whether the CLI is up-to-date [aliases: --update]

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
      --show-thinking
          Prints the Sec-Gemini thinking steps

          [env: SEC_GEMINI_SHOW_THINKING=]

      --api-key <API_KEY>
          Sec-Gemini API key

          [env: SEC_GEMINI_API_KEY=]

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
