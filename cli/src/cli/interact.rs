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

use std::collections::{HashMap, HashSet};
use std::fmt::Write;
use std::sync::Arc;
use std::time::Duration;

use colored::Colorize;
use dialoguer::Input;
use indicatif::ProgressBar;
use tokio::task::spawn_blocking;
use url::Url;

use crate::cli::markdown::try_render_markdown;
use crate::sdk::types::{
    LocalToolRequest, LocalToolResponse, Message, MessageBuilder, MessageType, State,
};
use crate::sdk::{Sdk, Session};
use crate::{config, or_fail, tool};

mod cmds;

#[derive(clap::Args)]
pub struct Options {
    /// Prints the Sec-Gemini thinking steps.
    #[arg(long, require_equals = true, env = "SEC_GEMINI_SHOW_THINKING")]
    show_thinking: Option<Option<bool>>,

    /// Sec-Gemini API key.
    #[arg(long, env = "SEC_GEMINI_API_KEY")]
    api_key: Option<String>,

    /// Provides Sec-Gemini access to these local tools.
    ///
    /// The format is a space- or comma-separated list of tool prefixes optionally preceded by an
    /// exclamation mark (to disable instead of enable). The list is evaluated from the first
    /// prefix in order until the last prefix. Initially, all tools are assumed enabled.
    ///
    /// For example, the empty string enables all tools, an exclamation mark disables all tools,
    /// `!,file,!file_write` would only enable `file` tools (like `file_read` or `file_sha256`)
    /// that are not `file_write`, and `!net net_tcp` would disable network tools except
    /// `net_tcp` ones.
    #[arg(long, env = "SEC_GEMINI_LOCAL_TOOL_ENABLE")]
    local_tool_enable: Option<String>,

    /// When to ask before executing a local tool.
    #[arg(long, env = "SEC_GEMINI_LOCAL_TOOL_ASK_BEFORE")]
    local_tool_ask_before: Option<config::LocalToolAsk>,

    /// Whether to ask for sending the response after executing a local tool.
    #[arg(long, env = "SEC_GEMINI_LOCAL_TOOL_ASK_AFTER")]
    local_tool_ask_after: Option<bool>,

    /// How long a local tool can run before sending the output to Sec-Gemini.
    #[arg(long, env = "SEC_GEMINI_LOCAL_TOOL_TIMEOUT")]
    local_tool_timeout: Option<cyborgtime::Duration>,

    /// How long a local tool can idle before sending the output to Sec-Gemini.
    #[arg(long, env = "SEC_GEMINI_LOCAL_TOOL_IDLE_TIME")]
    local_tool_idle_time: Option<cyborgtime::Duration>,

    /// Sec-Gemini base URL.
    #[arg(hide = true, long, env = "SEC_GEMINI_BASE_URL")]
    base_url: Option<Url>,
}

impl Options {
    pub async fn query(mut self, query: &str) {
        self.resolve().await;
        let sdk = Arc::new(Sdk::new(false).await);
        let mut session = get_session(sdk.clone()).await;
        self.execute(query, &mut session).await
    }

    pub async fn session(mut self) {
        self.resolve().await;
        let sdk = Arc::new(Sdk::new(true).await);
        let mut session = Session::new(sdk.clone(), String::new()).await;
        let interface = Arc::new(or_fail(linefeed::Interface::new("sec-gemini")));
        let style = "\0".bold().blue().to_string();
        let (start, clear) = style.split_once('\0').unwrap();
        or_fail(interface.set_prompt(&format!("\x01{clear}\x02> \x01{start}\x02")));
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
                    start,
                    clear,
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
        if let Some(x) = &self.local_tool_enable {
            config::LOCAL_TOOL_ENABLE.set_user(x.clone());
        }
        if let Some(x) = self.local_tool_ask_before {
            config::LOCAL_TOOL_ASK_BEFORE.set_user(x);
        }
        if let Some(x) = self.local_tool_ask_after {
            config::LOCAL_TOOL_ASK_AFTER.set_user(x);
        }
        if let Some(x) = self.local_tool_timeout {
            config::LOCAL_TOOL_TIMEOUT.set_user(x);
        }
        if let Some(x) = self.local_tool_idle_time {
            config::LOCAL_TOOL_IDLE_TIME.set_user(x);
        }
        if let Some(x) = &self.base_url {
            config::BASE_URL.set_user(x.clone());
        }
    }

    async fn execute(&mut self, query: &str, session: &mut Session) {
        let mut progress = new_progress();
        session.send(query).await;
        set_message(&progress, "Waiting response");
        let mut result: Option<String> = None;
        while let Some(message) = session.recv().await {
            if message.state == State::End {
                progress.finish_and_clear();
                let Some(content) = result.take() else {
                    log::warn!("no result before end");
                    break;
                };
                println!("{}", try_render_markdown(&content).trim_end());
                break;
            }
            let content = message.content.unwrap_or_default();
            match message.message_type {
                MessageType::LocalToolCall => {
                    progress.finish_and_clear();
                    let response = call_tool(&content, session).await;
                    progress = new_progress();
                    session.send_message(response).await;
                }
                MessageType::Result if message.status_code != 200 => (),
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

async fn get_session(sdk: Arc<Sdk>) -> Session {
    const SESSION_NAME: &str = "sec-gemini query";
    let enable = crate::tool::Enable::parse().await;
    let mut tools = crate::tool::Tools::list();
    tools.retain(|x| enable.check(x));
    let expected: HashSet<&str> = tools.iter().map(|(x, _)| x).collect();
    let mut best = None;
    let sessions = sdk.cached_sessions().await;
    for session in sessions.iter() {
        if session.name != SESSION_NAME {
            continue;
        }
        let actual: HashSet<&str> = session.local_tools.iter().map(|x| x.name.as_str()).collect();
        if actual != expected {
            continue;
        }
        match best {
            Some((best_time, _, _)) if session.create_time < best_time => (),
            _ => best = Some((session.create_time, &session.id, &session.local_tools)),
        }
    }
    if let Some((_, id, local_tools)) = best {
        log::info!("Resuming existing CLI session.");
        Session::resume(sdk.clone(), id.clone(), local_tools)
    } else {
        drop(sessions);
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

async fn call_tool(content: &str, session: &Session) -> Message {
    execution_marker("Start");
    let mut name = String::new();
    let (output, is_error) = match call_tool_(&mut name, content, session).await {
        Ok(x) => (x, None),
        Err(e) => (e, Some(true)),
    };
    let mut response = LocalToolResponse { name, output, is_error };
    let serialized = serde_json::to_string(&response)
        .or_else(|e| {
            response.output = e.to_string();
            response.is_error = Some(true);
            serde_json::to_string(&response)
        })
        .unwrap();
    let message = MessageBuilder::new(MessageType::LocalToolResult)
        .content(Some(serialized))
        .mime_type(Some("text/serialized-json".to_string()))
        .status_code(if is_error.is_some() { 500 } else { 200 })
        .build();
    execution_marker("End");
    message
}

async fn call_tool_(name: &mut String, content: &str, session: &Session) -> Result<String, String> {
    let args: LocalToolRequest = serde_json::from_str(content).map_err(|e| e.to_string())?;
    *name = args.tool_name;
    let tool = session.tool(name).ok_or_else(|| "tool not found".to_string())?;
    let args = (tool.reorder)(args.tool_args).await?.0;
    let command = display_tool_request(name, &args);
    let (kind, do_not_ask) = match tool.effect {
        tool::Effect::ReadOnly => ("read-only".green(), config::LocalToolAsk::Mutating),
        tool::Effect::Mutating => ("mutating".yellow(), config::LocalToolAsk::Destructive),
        tool::Effect::Destructive => ("destructive".red(), config::LocalToolAsk::Never),
    };
    print!("Sec-Gemini wants to execute a {kind} local tool on your machine:\n{command}");
    authorize(&config::LOCAL_TOOL_ASK_BEFORE, |x| authorize_tool(x, tool.effect), do_not_ask)
        .await?;
    let result = (tool.call)(args).await;
    let (success, output) = match &result {
        Ok(x) => ("successful".green(), display_tool_response(&x.0)),
        Err(e) => ("failed".bold().red(), format!("{}\n", e.red())),
    };
    print!("Sec-Gemini wants to access the result of the {success} execution:\n{output}");
    authorize(&config::LOCAL_TOOL_ASK_AFTER, |x| !x, false).await?;
    result.map(convert_tool_response)
}

fn display_tool_request(name: &str, args: &serde_json::Value) -> String {
    let mut result = format!("{}()\n", name.bold().yellow());
    if let Some(obj) = args.as_object() {
        display_json_object(&mut result, colored::Color::Yellow, obj);
    } else {
        writeln!(result, " {}", serde_json::to_string(args).unwrap().yellow()).unwrap();
    }
    result
}

fn display_tool_response(resp: &serde_json::Value) -> String {
    let mut result = String::new();
    match resp {
        serde_json::Value::String(x) => {
            write!(result, "{}", x.blue()).unwrap();
            ensure_newline(x, &mut result);
        }
        serde_json::Value::Object(x) => display_json_object(&mut result, colored::Color::Blue, x),
        x => fail!("unexpected response {x:?}"),
    }
    result
}

fn display_json_object(
    out: &mut String, color: colored::Color, map: &serde_json::Map<String, serde_json::Value>,
) {
    for (key, val) in map {
        write!(out, "{}:", key.bold().color(color)).unwrap();
        if let Some(val) = val.as_str() {
            if val.find('\n').is_some_and(|i| i + 1 < val.len()) {
                write!(out, "\n{}", val.color(color)).unwrap();
                ensure_newline(val, out);
                continue;
            }
        }
        writeln!(out, " {}", serde_json::to_string(val).unwrap().color(color)).unwrap();
    }
}

fn ensure_newline(val: &str, out: &mut String) {
    if !val.ends_with('\n') {
        or_fail(writeln!(out, "%"));
    }
}

fn convert_tool_response(response: rmcp::Json<serde_json::Value>) -> String {
    match response.0 {
        serde_json::Value::String(x) => x,
        x => serde_json::to_string(&x).unwrap(),
    }
}

fn execution_marker(verb: &str) {
    let line = format!("=== {verb} local tool interaction");
    println!("{}", line.bold().purple());
}

async fn authorize<T: Clone + std::str::FromStr + std::fmt::Display>(
    config: &config::Config<T>, decide: impl FnOnce(T) -> bool, do_not_ask: T,
) -> Result<(), String>
where <T as std::str::FromStr>::Err: std::error::Error {
    let (value, source) = config.get().await;
    if decide(value.clone()) {
        println!("Authorized by {}={value} (read from {source})", config.name());
        return Ok(());
    }
    let prompt = format!(
        "Type {} to authorize ({} to not ask again) or {} to deny",
        "yes".green(),
        "always".yellow(),
        "no".red(),
    );
    loop {
        let value: String = try_to!(
            "read authorization from terminal",
            Input::new().with_prompt(&prompt).interact_text(),
        );
        match value.as_str() {
            "yes" => break Ok(()),
            "always" => {
                config.set_user(do_not_ask);
                break Ok(());
            }
            "no" => break Err("tool permission denied".to_string()),
            _ => (),
        }
    }
}

fn authorize_tool(when: config::LocalToolAsk, effect: tool::Effect) -> bool {
    match when {
        config::LocalToolAsk::Never => true,
        config::LocalToolAsk::Destructive => effect != tool::Effect::Destructive,
        config::LocalToolAsk::Mutating => effect == tool::Effect::ReadOnly,
        config::LocalToolAsk::Always => false,
    }
}

#[test]
fn authorize_tool_ok() {
    use config::LocalToolAsk::*;
    use tool::Effect;

    // Ask never means always authorize.
    assert!(authorize_tool(Never, Effect::ReadOnly));
    assert!(authorize_tool(Never, Effect::Mutating));
    assert!(authorize_tool(Never, Effect::Destructive));

    // Ask destructive means authorize everything but destructive.
    assert!(authorize_tool(Destructive, Effect::ReadOnly));
    assert!(authorize_tool(Destructive, Effect::Mutating));
    assert!(!authorize_tool(Destructive, Effect::Destructive));

    // Ask mutating means only authorize read-only.
    assert!(authorize_tool(Mutating, Effect::ReadOnly));
    assert!(!authorize_tool(Mutating, Effect::Mutating));
    assert!(!authorize_tool(Mutating, Effect::Destructive));

    // Ask always means never authorize.
    assert!(!authorize_tool(Always, Effect::ReadOnly));
    assert!(!authorize_tool(Always, Effect::Mutating));
    assert!(!authorize_tool(Always, Effect::Destructive));
}
