// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use std::io::ErrorKind;

use clap::Parser;

mod completion;
mod config;
mod interact;
mod markdown;

/// Sec-Gemini swiss-army knife.
///
/// Sec-Gemini is an experimental cybersecurity-focused AI from Google. This CLI provides multiple
/// ways to interact with Sec-Gemini from the command-line.
#[derive(Parser)]
#[command(version)]
pub struct Action {
    #[command(subcommand)]
    command: Option<Command>,

    #[command(flatten)]
    options: interact::Options,

    /// The query to ask Sec-Gemini (interactive session if omitted).
    ///
    /// If the query is omitted, an interactive session is started where multiple queries can be
    /// asked successively.
    ///
    /// The query may be split across multiple arguments, in which case they will be separated by
    /// spaces. The following invocations are equivalent (with common shell escaping):
    ///
    ///     sec-gemini what is a CVE
    ///     sec-gemini 'what is a CVE'
    ///     sec-gemini   'what is'     a\ CVE
    query: Vec<String>,
}

#[derive(clap::Subcommand)]
#[command(args_conflicts_with_subcommands = true)]
#[command(disable_help_subcommand = true)]
enum Command {
    /// Reads, writes, or deletes configuration files.
    #[command(name = "--config")]
    Config(config::Action),

    /// Opens the Sec-Gemini web UI in a browser.
    #[command(name = "--open-ui", visible_alias = "--ui")]
    OpenUi,

    /// Updates the CLI if a newer version exists.
    #[command(name = "--self-update", visible_alias = "--update")]
    SelfUpdate,

    /// Generates a shell completion file.
    #[command(name = "--generate-completion", visible_alias = "--completion")]
    Completion(completion::Action),

    /// Renders a markdown input as if it was a Sec-Gemini output.
    #[command(hide = true, name = "--render-markdown")]
    RenderMarkdown(markdown::Action),
}

impl Action {
    pub async fn run(self) {
        if let Some(x) = self.command {
            return x.run().await;
        }
        let query = self.query.join(" ");
        match query.len() {
            0 => self.options.session().await,
            1 ..= 3 => fail!("the query is too short"),
            _ => self.options.query(&query).await,
        }
    }
}

impl Command {
    async fn run(self) {
        match self {
            Command::Config(x) => x.run().await,
            Command::OpenUi => {
                try_to!("open browser", opener::open_browser("https://ui.secgemini.google/"))
            }
            Command::SelfUpdate => {
                let mut update = tokio::process::Command::new("sec-gemini-update");
                match update.status().await {
                    Ok(status) => std::process::exit(status.code().unwrap_or(0)),
                    Err(err) if err.kind() == ErrorKind::NotFound => fail!("updater not found"),
                    Err(err) => fail!("failed to self update", &err),
                }
            }
            Command::Completion(x) => x.run().await,
            Command::RenderMarkdown(x) => x.run(),
        }
    }
}

#[test]
fn test() {
    <Action as clap::CommandFactory>::command().debug_assert();
}
