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

use std::fmt::Write;
use std::sync::Arc;
use std::time::Duration;

use colored::Colorize;
use indicatif::ProgressBar;
use linefeed::{Interface, ReadResult};
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender, unbounded_channel};
use url::Url;

use crate::cli::markdown::try_render_markdown;
use crate::config::Config;
use crate::or_fail;
use crate::sdk::types::{Message, MessageType, PublicSession};
use crate::sdk::{Sdk, Session};
use crate::util::choose;

mod name;

#[derive(clap::Args)]
pub struct Options {
    /// Prints the Sec-Gemini thinking steps.
    #[arg(long, env = "SEC_GEMINI_SHOW_THINKING")]
    show_thinking: bool,

    /// Sec-Gemini API key.
    #[arg(long, env = "SEC_GEMINI_API_KEY")]
    api_key: Option<String>,

    /// Sec-Gemini base URL.
    #[arg(hide = true, long, default_value = "https://api.secgemini.google")]
    base_url: Url,
}

impl Options {
    pub async fn query(self, query: &str) {
        let (sdk, sessions) = Sdk::new(self.sdk_options(false)).await;
        let (send, mut recv) = unbounded_channel::<Message>();
        let session = get_session(Arc::new(sdk), sessions, send).await;
        self.execute(query, &mut recv, &session).await
    }

    pub async fn session(self) {
        let (sdk, _) = Sdk::new(self.sdk_options(true)).await;
        let (send, mut recv) = unbounded_channel::<Message>();
        let name = format!("{}-{}", choose(name::ADJS), choose(name::TERMS));
        println!("Session: {}", name.cyan());
        let session = Session::new(Arc::new(sdk), name, send).await;
        let interface = Arc::new(or_fail(Interface::new("sec-gemini")));
        let style = "\0".bold().blue().to_string();
        let (start, clear) = style.split_once('\0').unwrap();
        or_fail(interface.set_prompt(&format!("{clear}> {start}")));
        loop {
            let line = or_fail(interface.read_line());
            or_fail(write!(interface, "{clear}"));
            let query = match line {
                ReadResult::Eof => break,
                ReadResult::Input(x) => x,
                ReadResult::Signal(x) => unreachable!("{x:?}"),
            };
            if query.trim().is_empty() {
                continue;
            }
            self.execute(&query, &mut recv, &session).await;
            interface.add_history(query);
        }
    }

    fn sdk_options(&self, interactive: bool) -> crate::sdk::Options {
        let api_key = match &self.api_key {
            Some(x) => Config::frozen(x.clone()),
            None => Config::unknown(&crate::config::API_KEY),
        };
        let base_url = self.base_url.clone();
        crate::sdk::Options { api_key, base_url, interactive }
    }

    async fn execute(&self, query: &str, recv: &mut UnboundedReceiver<Message>, session: &Session) {
        let progress = ProgressBar::new_spinner();
        set_message(&progress, "Sending request");
        progress.enable_steady_tick(Duration::from_millis(200));
        session.send(query);
        set_message(&progress, "Waiting response");
        while let Some(message) = recv.recv().await {
            let content = message.content.unwrap_or_default();
            match message.message_type {
                MessageType::Result => {
                    progress.finish_and_clear();
                    println!("{}", try_render_markdown(&content).trim_end());
                    break;
                }
                MessageType::Info => set_message(&progress, &content),
                MessageType::Thinking if self.show_thinking => {
                    let mut thinking = String::new();
                    thinking.push_str(&"Thinking".bold().yellow().to_string());
                    thinking.push('(');
                    thinking.push_str(&message.actor);
                    thinking.push_str("): ");
                    if let Some(subtype) = message.message_sub_type {
                        write!(thinking, "[{subtype}] ").unwrap();
                    }
                    thinking.push_str(&content);
                    progress.println(thinking);
                }
                MessageType::Error => fail!("{content}"),
                _ => (),
            }
        }
    }
}

async fn get_session(
    sdk: Arc<Sdk>, sessions: Vec<PublicSession>, send: UnboundedSender<Message>,
) -> Session {
    const SESSION_NAME: &str = "sec-gemini query";
    let mut best = None;
    for session in sessions {
        if session.name != SESSION_NAME {
            continue;
        }
        match best {
            Some((best_time, _)) if session.create_time < best_time => (),
            _ => best = Some((session.create_time, session.id)),
        }
    }
    if let Some((_, id)) = best {
        log::info!("Resuming existing CLI session.");
        Session::resume(&sdk, id, send).await
    } else {
        log::info!("Creating new CLI session.");
        Session::new(sdk, SESSION_NAME.to_string(), send).await
    }
}

fn set_message(progress: &ProgressBar, message: &str) {
    progress.set_message(message.bold().cyan().to_string());
}
