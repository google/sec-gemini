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
use std::fmt::Write;
use std::process::{ExitStatus, Stdio};

use colored::Colorize as _;
use dialoguer::Input;
use tokio::io::{AsyncReadExt as _, AsyncWriteExt};
use tokio::process::{Child, ChildStderr, ChildStdin, ChildStdout, Command};

use crate::cli::markdown::try_render_markdown;
use crate::config;

#[derive(Default)]
pub struct State(StateImpl);

#[derive(Default)]
enum StateImpl {
    #[default]
    Ready,
    Running(Box<Running>),
}

impl State {
    pub async fn update_query<'a>(&self, query: &'a str) -> (bool, Cow<'a, str>) {
        if !config::SHELL_ENABLE.get().await.0.guess(console::user_attended) {
            return (false, query.into());
        }
        if matches!(self.0, StateImpl::Running(_)) {
            let mut msg = format!("{query}\nThis is a reminder that there is a running command.");
            append_running_command(&mut msg);
            return (true, msg.into());
        }
        (
            true,
            format!(
                "{query}\n
If you need to run a command on my machine, use the format described at the end of my message.
I will pass <command> to `sh -c` in my shell and send you the exit status, standard output, and
standard error (truncated to a thousand bytes each).
If the command doesn't terminate and produces too much output, I will send you whatever is
available and you will be able to continue interacting with it.
You can explain why you want to run that command and what it does before the format.
But end your message immediately after <command>, don't add any more text.
If you need any information retrievable by running a command (like the system I'm running), run the
command to retrieve the information instead of asking me for the information. It's ok if a
command fails.
The format is:
{EXEC_SHELL_CMD}<command>"
            )
            .into(),
        )
    }

    pub async fn interpret_result(&mut self, content: &str) -> Option<String> {
        if let Some(command) = split_command(content, EXEC_SHELL_CMD) {
            self.execution_marker(Ok(true));
            let response = self.execute_shell_command(command).await;
            self.execution_marker(Ok(false));
            return Some(response);
        }
        if let Some(empty) = split_command(content, KILL_SHELL_CMD) {
            if empty.trim_end().is_empty() {
                self.kill().await;
                self.execution_marker(Err("Kill"));
                return Some("The shell command has been killed.".to_string());
            }
        }
        if let Some(input) = split_command(content, CONT_SHELL_CMD) {
            if let Some(running) = self.take() {
                let input = input.trim_end().strip_suffix(".").unwrap_or(input);
                self.execution_marker(Err("Resume"));
                let response = self.run_shell_command(running, input).await;
                self.execution_marker(Ok(false));
                return Some(response);
            }
        }
        None
    }

    fn execution_marker(&self, start: Result<bool, &str>) {
        let keyword = match (start, &self.0) {
            (Err(x), _) => x,
            (Ok(true), StateImpl::Ready) => "Start",
            (Ok(true), StateImpl::Running(_)) => "Replace",
            (Ok(false), StateImpl::Ready) => "End",
            (Ok(false), StateImpl::Running(_)) => "Suspend",
        };
        let line = format!("=== {keyword} shell command execution");
        println!("{}", line.bold().purple());
    }

    async fn execute_shell_command(&mut self, mut command: &str) -> String {
        self.kill().await;
        command = command.strip_suffix("\n").unwrap_or(command);
        if let Some(candidate) = command.strip_prefix("`") {
            if let Some(clean) = candidate.strip_suffix("`") {
                command = clean;
            }
        }
        println!(
            "Sec-Gemini wants to execute the following command on your machine:\n{}",
            command.yellow()
        );
        if let Some(error) = authorize(&config::SHELL_AUTO_EXEC).await {
            return error;
        }
        let mut check_timeout = true;
        let mut check_idle = true;
        if command.starts_with("sudo ") {
            // We need to give the user time in case they need to type their password.
            check_timeout = false;
            check_idle = false;
        }
        let mut child = try_to!(
            "execute shell command",
            Command::new("sh")
                .args(["-c", command])
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
        );
        let running = Box::new(Running {
            check_timeout,
            check_idle,
            stdin: child.stdin.take().unwrap(),
            stdout: child.stdout.take().unwrap(),
            stderr: child.stderr.take().unwrap(),
            child,
            output: Buffer::default(),
            error: Buffer::default(),
        });
        self.run_shell_command(running, "").await
    }

    async fn run_shell_command(&mut self, mut running: Box<Running>, input: &str) -> String {
        if !input.is_empty() {
            print!(
                "Sec-Gemini wants to write the following input to the command:\n{}",
                input.blue()
            );
            if !input.ends_with("\n") {
                println!("%");
            }
            if let Some(error) = authorize(&config::SHELL_AUTO_WRITE).await {
                return error;
            }
            match running.stdin.write_all(input.as_bytes()).await {
                Ok(()) => (),
                Err(err) => {
                    log::debug!("failed to write stdin: {err}");
                    return self.process_outcome(running, Outcome::Error).await;
                }
            }
        }
        let idle_time = *config::SHELL_IDLE_TIME.get().await.0;
        let timeout = tokio::time::sleep(*config::SHELL_TIMEOUT.get().await.0);
        tokio::pin!(timeout);
        let outcome = loop {
            tokio::select! {
                () = &mut timeout, if running.check_timeout => break Outcome::Timeout,
                () = tokio::time::sleep(idle_time), if running.check_idle => break Outcome::Idle,
                len = running.stdout.read(running.output.read()) => {
                    match len {
                        Ok(len) => running.output.advance(len),
                        Err(err) => {
                            log::debug!("failed to read stdout: {err}");
                            break Outcome::Error;
                        },
                    }
                }
                len = running.stderr.read(running.error.read()) => {
                    match len {
                        Ok(len) => running.error.advance(len),
                        Err(err) => {
                            log::debug!("failed to read stderr: {err}");
                            break Outcome::Error;
                        },
                    }
                }
                status = running.child.wait() => match status {
                    Ok(status) => break Outcome::Exit(status),
                    Err(err) => {
                        log::debug!("failed to wait for child: {err}");
                        break Outcome::Error;
                    },
                }
            }
            if running.output.is_full() || running.error.is_full() {
                break Outcome::Full;
            }
        };
        self.process_outcome(running, outcome).await
    }

    async fn process_outcome(&mut self, mut running: Box<Running>, outcome: Outcome) -> String {
        let mut response = match outcome {
            Outcome::Exit(status) => match status.code() {
                _ if status.success() => "The command succeeded".to_string(),
                None => "The command failed".to_string(),
                Some(code) => format!("The command failed with exit code {code}"),
            },
            Outcome::Timeout => format!(
                "The command is still running after {}",
                config::SHELL_TIMEOUT.get().await.0
            ),
            Outcome::Idle => format!(
                "The command has been idle for {} and is still running",
                config::SHELL_IDLE_TIME.get().await.0
            ),
            Outcome::Error => "The command execution failed".to_string(),
            Outcome::Full => "The command is still running and can produce more output".to_string(),
        };
        writeln!(response, ".").unwrap();
        running.output.extract(&mut response, "standard output");
        running.error.extract(&mut response, "standard error");
        print!(
            "Sec-Gemini wants to read the following result of the execution:\n{}",
            response.blue()
        );
        if let Some(error) = authorize(&config::SHELL_AUTO_READ).await {
            return error;
        }
        match outcome {
            Outcome::Timeout | Outcome::Idle | Outcome::Full => {
                self.0 = StateImpl::Running(running);
                append_running_command(&mut response);
            }
            Outcome::Error => try_to!("kill shell command", running.child.kill().await),
            Outcome::Exit(_) => (),
        }
        response
    }

    fn take(&mut self) -> Option<Box<Running>> {
        match std::mem::take(&mut self.0) {
            StateImpl::Ready => None,
            StateImpl::Running(running) => Some(running),
        }
    }

    async fn kill(&mut self) {
        if let Some(mut state) = self.take() {
            try_to!("kill shell command", state.child.kill().await);
        }
    }
}

const EXEC_SHELL_CMD: &str = "Execute shell command: ";
const KILL_SHELL_CMD: &str = "Kill shell command.";
const CONT_SHELL_CMD: &str = "Resume shell command: ";

struct Running {
    check_timeout: bool,
    check_idle: bool,
    child: Child,
    stdin: ChildStdin,
    stdout: ChildStdout,
    stderr: ChildStderr,
    output: Buffer,
    error: Buffer,
}

struct Buffer {
    len: usize,
    data: [u8; 1024],
}

#[derive(Clone, Copy)]
enum Outcome {
    Exit(ExitStatus),
    Timeout,
    Idle,
    Error,
    Full,
}

impl Default for Buffer {
    fn default() -> Self {
        Buffer { len: 0, data: [0; 1024] }
    }
}

impl Buffer {
    fn is_empty(&self) -> bool {
        self.len == 0
    }

    fn is_full(&self) -> bool {
        self.len == self.data.len()
    }

    fn read(&mut self) -> &mut [u8] {
        &mut self.data[self.len ..]
    }

    fn advance(&mut self, len: usize) {
        self.len += len;
    }

    fn extract(&mut self, resp: &mut String, name: &str) {
        if self.is_empty() {
            return writeln!(resp, "There is no {name}.").unwrap();
        }
        // Try to find the last UTF-8 character boundary (supporting malformed UTF-8). The only case
        // where len is smaller than self.len is when we a UTF-8 character is cut in the middle.
        let mut len = self.len;
        while 0 < len {
            len -= 1;
            let n = match self.data[len] {
                x if x & 0x80 == 0x00 => 1,
                x if x & 0xc0 == 0x80 => continue,
                x if x & 0xe0 == 0xc0 => 2,
                x if x & 0xf0 == 0xe0 => 3,
                x if x & 0xf8 == 0xf0 => 4,
                _ => 0,
            };
            if len + n <= self.len {
                len = self.len;
            }
            break;
        }
        let text = String::from_utf8_lossy(&self.data[.. len]);
        if len < self.len || self.is_full() {
            writeln!(resp, "The {name} (truncated to {len} bytes) is:\n{text}").unwrap();
        } else {
            writeln!(resp, "The {name} is:\n{text}").unwrap();
        }
        if resp.ends_with("\n\n") {
            let _ = resp.pop();
        }
        self.data.copy_within(len .. self.len, 0);
        self.len -= len;
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

fn append_running_command(msg: &mut String) {
    write!(
        msg,
        "
If you don't need to interact with the running command anymore, you can kill it by ending your
message with:
{KILL_SHELL_CMD}
If you need to further interact with the running command, you have different options.
If you just want to read more output, you can end your message with:
{CONT_SHELL_CMD}.
If you also want send input before reading more output, you can end your message with:
{CONT_SHELL_CMD}<input>.
In particular, if your input must end with a newline, the dot should be on its own line, like this:
{CONT_SHELL_CMD}This is an example input line ending with a newline
.
In all those cases, your message must end with a dot (which is not part of the input)."
    )
    .unwrap();
}

fn split_command<'a>(content: &'a str, command: &str) -> Option<&'a str> {
    if !content.contains(command) {
        return None;
    }
    let (prefix, suffix) = content.split_once(command).unwrap();
    // This is a best-effort detection that the command looks like a command. The most common issue
    // is Sec-Gemini asking to execute multiple commands.
    if suffix.contains(command) {
        return None;
    }
    if !prefix.is_empty() {
        println!("{}", try_render_markdown(prefix).trim_end());
    }
    log::info!("{command}{suffix:?}");
    Some(suffix)
}
