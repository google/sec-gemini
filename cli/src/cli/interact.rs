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

use std::borrow::Cow;
use std::collections::HashMap;
use std::fmt::Write;
use std::sync::Arc;
use std::time::Duration;

use colored::Colorize;
use dialoguer::Input;
use indicatif::ProgressBar;
use tokio::process::Command;
use tokio::task::spawn_blocking;
use url::Url;

use crate::cli::markdown::try_render_markdown;
use crate::sdk::types::{MessageType, PublicSession};
use crate::sdk::{Sdk, Session};
use crate::{config, or_fail};

mod cmds;

#[derive(clap::Args)]
pub struct Options {
    /// Prints the Sec-Gemini thinking steps.
    #[arg(long, require_equals = true, env = "SEC_GEMINI_SHOW_THINKING")]
    show_thinking: Option<Option<bool>>,

    /// Sec-Gemini API key.
    #[arg(long, env = "SEC_GEMINI_API_KEY")]
    api_key: Option<String>,

    /// Whether Sec-Gemini can ask to execute shell commands.
    #[arg(long, env = "SEC_GEMINI_ENABLE_SHELL")]
    enable_shell: Option<config::AutoBool>,

    /// Whether Sec-Gemini can execute shell commands without confirmation.
    #[arg(long, env = "SEC_GEMINI_AUTO_EXEC")]
    auto_exec: Option<bool>,

    /// Whether results of shell commands are sent to Sec-Gemini without confirmation.
    #[arg(long, env = "SEC_GEMINI_AUTO_SEND")]
    auto_send: Option<bool>,

    /// Sec-Gemini base URL.
    #[arg(hide = true, long, env = "SEC_GEMINI_BASE_URL")]
    base_url: Option<Url>,
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
                    this: &self,
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
        if let Some(x) = self.enable_shell {
            config::ENABLE_SHELL.set_user(x);
        }
        if let Some(x) = &self.base_url {
            config::BASE_URL.set_user(x.clone());
        }
    }

    async fn execute(&self, query: &str, session: &mut Session) {
        let mut progress = new_progress();
        let enable_shell = config::ENABLE_SHELL.get().await.0.guess(console::user_attended);
        let query: Cow<'_, str> = if enable_shell {
            format!(
                "{query}\n
If you need to run a command on my machine, use the format described at the end of my message.
I will pass <command> to `sh -c` in my shell and send you the exit status, standard output, and
standard error (truncated to a thousand bytes each).
End your message immediately after <command>, don't add any more text.
You can explain why you want to run that command and what it does before the format.
If you need any information retrievable by running a command (like the system I'm running), run the
command to retrieve the information instead of asking me for the information.
The format is:
{EXEC_SHELL_CMD}<command>"
            )
            .into()
        } else {
            query.into()
        };
        session.send(&query);
        set_message(&progress, "Waiting response");
        while let Some(message) = session.recv().await {
            let content = message.content.unwrap_or_default();
            match message.message_type {
                MessageType::Result if enable_shell && content.contains(EXEC_SHELL_CMD) => {
                    progress.finish_and_clear();
                    let (prefix, command) = content.split_once(EXEC_SHELL_CMD).unwrap();
                    // This is a best-effort detection that the command looks like a command. The
                    // most common issue is Sec-Gemini asking to execute multiple commands.
                    if command.contains(EXEC_SHELL_CMD) {
                        println!("{}", try_render_markdown(&content).trim_end());
                        break;
                    }
                    if !prefix.is_empty() {
                        println!("{}", try_render_markdown(prefix).trim_end());
                    }
                    println!("{}", "=== Enter shell command execution flow".bold().purple());
                    let response = execute_shell_command(command).await;
                    println!("{}", "=== Exit shell command execution flow".bold().purple());
                    progress = new_progress();
                    session.send(&response);
                }
                MessageType::Result => {
                    progress.finish_and_clear();
                    println!("{}", try_render_markdown(&content).trim_end());
                    break;
                }
                MessageType::Info => set_message(&progress, &content),
                MessageType::Thinking => {
                    if config::SHOW_THINKING.get().await.0 {
                        let mut thinking = String::new();
                        write!(thinking, "{}: ", "Thinking".bold().yellow()).unwrap();
                        if let Some(subtype) = message.message_sub_type {
                            let subtype = format!("[{subtype}]");
                            write!(thinking, "{} ", subtype.bold().yellow()).unwrap();
                        }
                        write!(thinking, "{}", content.trim_end().yellow()).unwrap();
                        progress.println(thinking);
                    }
                }
                MessageType::Error => fail!("{content}"),
                _ => (),
            }
        }
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
        Session::resume(&sdk, id.clone()).await
    } else {
        log::info!("Creating new CLI session.");
        Session::new(sdk, SESSION_NAME.to_string()).await
    }
}

fn set_message(progress: &ProgressBar, message: &str) {
    progress.set_message(message.bold().cyan().to_string());
}

const EXEC_SHELL_CMD: &str = "Execute shell command: ";

async fn execute_shell_command(command: &str) -> String {
    println!(
        "Sec-Gemini wants to execute the following command on your machine:\n{}",
        command.yellow()
    );
    if let Some(error) = authorize(&config::AUTO_EXEC).await {
        return error;
    }
    let output =
        try_to!("execute shell command", Command::new("sh").arg("-c").arg(command).output().await);
    let outcome: Cow<'_, str> = match output.status.code() {
        None => if output.status.success() { "succeeded" } else { "failed" }.into(),
        Some(0) => "succeeded".into(),
        Some(code) => format!("failed with exit code {code}").into(),
    };
    let mut response = format!("The command {outcome}. ");
    if output.stdout.is_empty() {
        writeln!(response, "There is no standard output.").unwrap();
    } else {
        extract(&mut response, "standard output", output.stdout);
    }
    if !output.stderr.is_empty() {
        extract(&mut response, "standard error", output.stderr);
    }
    print!("The result of the execution is:\n{}", response.blue());
    println!("Do you authorize sending this result to Sec-Gemini?");
    if let Some(error) = authorize(&config::AUTO_SEND).await {
        return error;
    }
    response
}

fn extract(resp: &mut String, name: &str, src: Vec<u8>) {
    let Ok(src) = String::from_utf8(src) else {
        return writeln!(resp, "The {name} was not UTF-8 and has been discarded.").unwrap();
    };
    let indices = src.char_indices().map(|(i, _)| i).chain(std::iter::once(src.len()));
    #[allow(clippy::double_ended_iterator_last)]
    let len = indices.filter(|&i| i <= 1000).last().unwrap();
    if len < src.len() {
        write!(resp, "The {name} was {} bytes long. ", src.len()).unwrap();
        writeln!(resp, "The first {len} bytes are:\n{}", &src[.. len]).unwrap();
    } else {
        writeln!(resp, "The {name} is:\n{src}").unwrap();
    }
    if resp.ends_with("\n\n") {
        let _ = resp.pop();
    }
}

async fn authorize(config: &config::Config<bool>) -> Option<String> {
    if let (true, source) = config.get().await {
        println!("Authorized by {} (read from {source})", config.name());
        return None;
    }
    let prompt = format!("Type {} to authorize or {} to deny", "yes".green(), "no".red());
    loop {
        let value: String = try_to!(
            "read authorization from terminal",
            Input::new().with_prompt(&prompt).interact_text(),
        );
        match value.as_str() {
            "yes" => break None,
            "no" => break Some("I deny you to execute this shell command.".to_string()),
            _ => (),
        }
    }
}

fn new_progress() -> ProgressBar {
    let progress = ProgressBar::new_spinner();
    set_message(&progress, "Sending request");
    progress.enable_steady_tick(Duration::from_millis(200));
    progress
}
