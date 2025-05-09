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

use std::ops::Deref;
use std::sync::OnceLock;

use clap::Parser;
use url::Url;

mod query;
mod session;

/// Sec-Gemini swiss-army knife.
///
/// Sec-Gemini is an experimental cybersecurity-focused AI from Google. This CLI provides multiple
/// ways to interact with Sec-Gemini from the command-line.
#[derive(Parser)]
#[command(version)]
pub struct Cli {
    #[command(flatten)]
    pub flags: Flags,

    #[command(subcommand)]
    pub action: Action,
}

#[test]
fn test_cli() {
    <Cli as clap::CommandFactory>::command().debug_assert();
}

pub struct GlobalFlags(OnceLock<Flags>);

impl Deref for GlobalFlags {
    type Target = Flags;

    fn deref(&self) -> &Self::Target {
        self.0.get().unwrap()
    }
}

impl GlobalFlags {
    pub fn set(&self, flags: Flags) {
        self.0.set(flags).ok().unwrap();
    }
}

pub static FLAGS: GlobalFlags = GlobalFlags(OnceLock::new());

#[derive(clap::Args)]
pub struct Flags {
    /// Sec-Gemini API key.
    #[arg(long, env = "SEC_GEMINI_API_KEY")]
    pub api_key: Option<String>,

    /// Prints the execution flow.
    #[arg(long, env = "SEC_GEMINI_EXECUTION_FLOW")]
    pub execution_flow: bool,

    /// Sec-Gemini base URL.
    #[arg(hide = true, long, default_value = "https://api.secgemini.google")]
    pub base_url: Url,

    /// Log level.
    #[arg(hide = true, long, default_value = "off")]
    pub log_level: String,
}

impl Flags {
    pub fn api_key(&self) -> &str {
        match &self.api_key {
            Some(x) => x,
            None => fail!(
                "Sec-Gemini API key is not set.

Set the --api-key flag or the SEC_GEMINI_API_KEY environment variable."
            ),
        }
    }
}

#[derive(clap::Subcommand)]
pub enum Action {
    Query(query::Action),
    Session(session::Action),
    /// Opens the Sec-Gemini web UI in a browser.
    WebUi,
}

impl Action {
    pub async fn run(self) {
        match self {
            Action::Query(x) => x.run().await,
            Action::Session(x) => x.run().await,
            Action::WebUi => match opener::open_browser("https://ui.secgemini.google/") {
                Ok(()) => (),
                Err(e) => fail!("Failed to open browser: {e}"),
            },
        }
    }
}
