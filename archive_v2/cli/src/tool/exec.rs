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

use std::process::Stdio;
use std::sync::Mutex;

use rmcp::Json;
use rmcp::handler::server::wrapper::Parameters;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::process::{Child, ChildStderr, ChildStdin, ChildStdout, Command};

use crate::config;
use crate::tool::Tools;

pub fn list(tools: &mut Tools) {
    tools.push(_spawn_tool_attr(), spawn);
    tools.push(_interact_tool_attr(), interact);
    tools.push(_kill_tool_attr(), kill);
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct SpawnRequest {
    program: String,
    arguments: Vec<String>,
    #[serde(flatten)]
    interact: InteractRequest,
}

/// Spawns a process with input and output interaction.
///
/// To interact with the process, use the `exec_interact` tool. To kill the program, use the
/// `exec_kill` tool. The initial interaction is built-in by taking the same `stdin` and
/// `close_stdin` fields as `exec_interact` and returning the same fields.
///
/// This tool can be used together with `file_write` (setting `executable` to create an executable
/// file) to execute a Python or shell script.
#[rmcp::tool(name = "exec_spawn")]
async fn _spawn(_: Parameters<SpawnRequest>) -> Result<Json<InteractResponse>, String> {
    // TODO(https://github.com/modelcontextprotocol/rust-sdk/issues/495): Remove when fixed.
    unreachable!()
}

async fn spawn(params: Parameters<SpawnRequest>) -> Result<Json<InteractResponse>, String> {
    let SpawnRequest { program, arguments, interact: request } = params.0;
    let mut child = Command::new(program)
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    let running = Running {
        stdin: Some(child.stdin.take().unwrap()),
        stdout: child.stdout.take().unwrap(),
        stderr: child.stderr.take().unwrap(),
        child,
    };
    *STATE.lock().unwrap() = Some(running);
    interact(Parameters(request)).await
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct InteractRequest {
    #[serde(default)]
    stdin: String,
    #[serde(default)]
    close_stdin: bool,
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct InteractResponse {
    running: bool,
    success: Option<bool>,
    stdout: String,
    stderr: String,
}

/// Interacts with a running process in textual form.
///
/// The `stdin` parameter will be written to the standard input of the process. It can be empty if
/// interacting for output only. When the `close_stdin` parameter is set, the standard input will be
/// closed. This is necessary for some programs to start processing. Note that once the standard
/// input is closed, future interactions must not set `stdin` to non-empty content.
///
/// In the response, the `running` field indicates whether the process is still running. When it's
/// not running anymore, the `success` field indicates if it terminated successfully or not. The
/// `stdout` and `stderr` fields contain the output read from the standard output and error since
/// the last interaction.
///
/// The tool will listen for output until some amount of inactivity or some fixed deadline,
/// whichever happens first. The tool will fail if the process outputs binary data that is not
/// UTF-8.
#[rmcp::tool(name = "exec_interact")]
async fn _interact(_: Parameters<InteractRequest>) -> Result<Json<InteractResponse>, String> {
    // TODO(https://github.com/modelcontextprotocol/rust-sdk/issues/495): Remove when fixed.
    unreachable!()
}

#[allow(clippy::await_holding_lock)]
async fn interact(params: Parameters<InteractRequest>) -> Result<Json<InteractResponse>, String> {
    let InteractRequest { stdin, close_stdin } = params.0;
    let mut state = STATE.lock().unwrap();
    let Some(running) = &mut *state else {
        return Err("no running process".to_string());
    };
    if !stdin.is_empty() {
        let Some(pipe) = running.stdin.as_mut() else { return Err("stdin is closed".to_string()) };
        pipe.write_all(stdin.as_bytes()).await.map_err(|e| e.to_string())?;
    }
    if close_stdin {
        let Some(mut pipe) = running.stdin.take() else {
            return Err("stdin is already closed".to_string());
        };
        pipe.shutdown().await.map_err(|e| e.to_string())?;
    }
    const SIZE: usize = 1024;
    let mut stdout = vec![0; SIZE];
    let mut stdout_len = 0;
    let mut stderr = vec![0; SIZE];
    let mut stderr_len = 0;
    let idle_time = *config::LOCAL_TOOL_IDLE_TIME.get().await.0;
    let timeout = tokio::time::sleep(*config::LOCAL_TOOL_TIMEOUT.get().await.0);
    tokio::pin!(timeout);
    let exited = loop {
        tokio::select! {
            biased;
            () = &mut timeout => break None,
            () = tokio::time::sleep(idle_time) => break None,
            len = running.stdout.read(&mut stdout[stdout_len..]),
            if stdout_len < stdout.len() => match len {
                Ok(0) => stdout.truncate(stdout_len),
                Ok(len) => {
                    stdout_len += len;
                    stdout.resize(stdout_len + SIZE, 0);
                }
                Err(e) => return Err(e.to_string()),
            },
            len = running.stderr.read(&mut stderr[stderr_len..]),
            if stderr_len < stderr.len() => match len {
                Ok(0) => stderr.truncate(stderr_len),
                Ok(len) => {
                    stderr_len += len;
                    stderr.resize(stderr_len + SIZE, 0);
                }
                Err(e) => return Err(e.to_string()),
            },
            status = running.child.wait() => match status {
                Ok(status) => break Some(status.success()),
                Err(e) => return Err(e.to_string()),
            },
        }
    };
    stdout.truncate(stdout_len);
    stderr.truncate(stderr_len);
    let stdout = String::from_utf8(stdout).map_err(|e| e.to_string())?;
    let stderr = String::from_utf8(stderr).map_err(|e| e.to_string())?;
    let (running, success) = match exited {
        None => (true, None),
        Some(success) => (false, Some(success)),
    };
    Ok(Json(InteractResponse { running, success, stdout, stderr }))
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct KillRequest {}

/// Kills an running process.
#[rmcp::tool(name = "exec_kill", annotations(destructive_hint = false))]
async fn _kill(_: Parameters<KillRequest>) -> Result<Json<String>, String> {
    unreachable!()
}

#[allow(clippy::await_holding_lock)]
async fn kill(params: Parameters<KillRequest>) -> Result<Json<String>, String> {
    let KillRequest {} = params.0;
    let Some(mut running) = STATE.lock().unwrap().take() else {
        return Err("no running process".to_string());
    };
    running.child.kill().await.map_err(|e| e.to_string())?;
    Ok(Json("killed".to_string()))
}

static STATE: Mutex<Option<Running>> = Mutex::new(None);

struct Running {
    stdin: Option<ChildStdin>,
    stdout: ChildStdout,
    stderr: ChildStderr,
    child: Child,
}
