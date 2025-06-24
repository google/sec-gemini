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

use std::collections::HashMap;
use std::fmt::Write;
use std::sync::Arc;
use std::time::Duration;

use colored::Colorize;
use indicatif::ProgressBar;
use tokio::task::spawn_blocking;
use url::Url;

use crate::cli::markdown::try_render_markdown;
use crate::sdk::types::{MessageType, PublicSession, State};
use crate::sdk::{Sdk, Session};
use crate::{config, or_fail};

mod cmds;
mod shell;

#[derive(clap::Args)]
pub struct Options {
    /// Prints the Sec-Gemini thinking steps.
    #[arg(long, require_equals = true, env = "SEC_GEMINI_SHOW_THINKING")]
    show_thinking: Option<Option<bool>>,

    /// Sec-Gemini API key.
    #[arg(long, env = "SEC_GEMINI_API_KEY")]
    api_key: Option<String>,

    /// Whether Sec-Gemini can ask to execute shell commands.
    #[arg(long, env = "SEC_GEMINI_SHELL_ENABLE")]
    shell_enable: Option<config::AutoBool>,

    /// Whether Sec-Gemini can ask to execute shell commands.
    #[arg(long, env = "SEC_GEMINI_SHELL_ENABLE")]
    shell_timeout: Option<cyborgtime::Duration>,

    /// Whether Sec-Gemini can execute shell commands without confirmation.
    #[arg(long, env = "SEC_GEMINI_SHELL_AUTO_EXEC")]
    shell_auto_exec: Option<bool>,

    /// Whether Sec-Gemini can read the result of shell commands without confirmation.
    #[arg(long, env = "SEC_GEMINI_SHELL_AUTO_READ")]
    shell_auto_read: Option<bool>,

    /// Whether Sec-Gemini can write input to shell commands without confirmation.
    #[arg(long, env = "SEC_GEMINI_SHELL_AUTO_WRITE")]
    shell_auto_write: Option<bool>,

    /// Sec-Gemini base URL.
    #[arg(hide = true, long, env = "SEC_GEMINI_BASE_URL")]
    base_url: Option<Url>,

    #[arg(skip)]
    shell: shell::State,
}

impl Options {
    pub async fn query(mut self, query: &str) {
        self.resolve().await;
        let sdk = Arc::new(Sdk::new(false).await);
        let mut session = get_session(sdk.clone(), &sdk.cached_sessions().await).await;
        self.execute(query, &mut session).await
    }

    pub async fn session(mut self) {
        self.resolve().await;
        let sdk = Arc::new(Sdk::new(true).await);
        let mut session = Session::new(sdk.clone(), String::new()).await;
        let interface = Arc::new(or_fail(linefeed::Interface::new("sec-gemini")));
        let style = "\0".bold().blue().to_string();
        let (start, clear) = style.split_once('\0').unwrap();
        or_fail(interface.set_prompt(&format!("{clear}> {start}")));
        let _ = interface.set_completer(Arc::new(cmds::Completer::new(sdk.clone())));
        loop {
            let line = try_to!(
                "read line",
                spawn_blocking({
                    let interface = interface.clone();
                    move || or_fail(interface.read_line())
                })
                .await
            );
            or_fail(write!(interface, "{clear}"));
            let query = match line {
                linefeed::ReadResult::Eof => break,
                linefeed::ReadResult::Input(x) => x,
                linefeed::ReadResult::Signal(x) => unreachable!("{x:?}"),
            };
            if query.trim().is_empty() {
                continue;
            }
            if let Some(query) = query.strip_prefix("/") {
                let input = cmds::CommandInput {
                    this: &mut self,
                    sdk: &sdk,
                    session: &mut session,
                    args: HashMap::new(),
                };
                cmds::execute_command(query, input).await;
            } else {
                self.execute(&query, &mut session).await;
            }
            interface.add_history(query);
        }
    }

    async fn resolve(&mut self) {
        if let Some(x) = self.show_thinking {
            config::SHOW_THINKING.set_user(x.unwrap_or(true));
        }
        if let Some(x) = &self.api_key {
            config::API_KEY.set_user(x.clone());
        }
        if let Some(x) = self.shell_enable {
            config::SHELL_ENABLE.set_user(x);
        }
        if let Some(x) = self.shell_timeout {
            config::SHELL_TIMEOUT.set_user(x);
        }
        if let Some(x) = self.shell_auto_exec {
            config::SHELL_AUTO_EXEC.set_user(x);
        }
        if let Some(x) = self.shell_auto_read {
            config::SHELL_AUTO_READ.set_user(x);
        }
        if let Some(x) = self.shell_auto_write {
            config::SHELL_AUTO_WRITE.set_user(x);
        }
        if let Some(x) = &self.base_url {
            config::BASE_URL.set_user(x.clone());
        }
    }

    async fn execute(&mut self, query: &str, session: &mut Session) {
        let (enable_shell, query) = self.shell.update_query(query).await;
        let mut progress = new_progress();
        session.send(&query).await;
        set_message(&progress, "Waiting response");
        let mut result: Option<String> = None;
        while let Some(message) = session.recv().await {
            if message.state == State::End {
                progress.finish_and_clear();
                let Some(content) = result.take() else {
                    log::warn!("no result before end");
                    break;
                };
                if enable_shell {
                    if let Some(response) = self.shell.interpret_result(&content).await {
                        progress = new_progress();
                        session.send(&response).await;
                        continue;
                    }
                }
                println!("{}", try_render_markdown(&content).trim_end());
                break;
            }
            let content = message.content.unwrap_or_default();
            match message.message_type {
                MessageType::Result if result.is_some() => log::warn!("multiple results"),
                MessageType::Result => result = Some(content),
                MessageType::Info => set_message(&progress, &content),
                MessageType::Thinking => {
                    if config::SHOW_THINKING.get().await.0 {
                        let mut thinking = String::new();
                        write!(thinking, "{}: ", "Thinking".bold().yellow()).unwrap();
                        if let Some(title) = message.title {
                            let title = format!("[{title}]");
                            write!(thinking, "{} ", title.bold().yellow()).unwrap();
                        }
                        write!(thinking, "{}", content.trim_end().yellow()).unwrap();
                        progress.println(thinking);
                    }
                }
                MessageType::Error => {
                    let mut error = String::new();
                    write!(error, "{}: ", "Error".bold().red()).unwrap();
                    write!(error, "{}", content.trim_end().red()).unwrap();
                    progress.println(error);
                }
                _ => (),
            }
        }
        session.done();
    }
}

async fn get_session(sdk: Arc<Sdk>, sessions: &[PublicSession]) -> Session {
    const SESSION_NAME: &str = "sec-gemini query";
    let mut best = None;
    for session in sessions {
        if session.name != SESSION_NAME {
            continue;
        }
        match best {
            Some((best_time, _)) if session.create_time < best_time => (),
            _ => best = Some((session.create_time, &session.id)),
        }
    }
    if let Some((_, id)) = best {
        log::info!("Resuming existing CLI session.");
        Session::resume(sdk, id.clone())
    } else {
        log::info!("Creating new CLI session.");
        Session::new(sdk, SESSION_NAME.to_string()).await
    }
}

fn set_message(progress: &ProgressBar, message: &str) {
    progress.set_message(message.bold().cyan().to_string());
}

fn new_progress() -> ProgressBar {
    let progress = ProgressBar::new_spinner();
    set_message(&progress, "Sending request");
    progress.enable_steady_tick(Duration::from_millis(200));
    progress
}
