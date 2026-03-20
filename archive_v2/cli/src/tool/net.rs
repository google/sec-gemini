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

use std::sync::Mutex;

use rmcp::Json;
use rmcp::handler::server::wrapper::Parameters;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

use crate::config;
use crate::tool::Tools;

pub fn list(tools: &mut Tools) {
    tools.push(_connect_tool_attr(), connect);
    tools.push(_interact_tool_attr(), interact);
    tools.push(_close_tool_attr(), close);
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct ConnectRequest {
    host: String,
    port: u16,
    input: String,
}

/// Opens a TCP connection to a remote host.
///
/// To interact with the connection, use the `net_tcp_interact` tool. To close the connection, use
/// the `net_tcp_close` tool. The initial interaction is built-in by taking the same `input` field
/// as `net_tcp_interact` and returning the same fields.
#[rmcp::tool(name = "net_tcp_connect", annotations(destructive_hint = false))]
async fn _connect(_: Parameters<ConnectRequest>) -> Result<Json<InteractResponse>, String> {
    // TODO(https://github.com/modelcontextprotocol/rust-sdk/issues/495): Remove when fixed.
    unreachable!()
}

async fn connect(params: Parameters<ConnectRequest>) -> Result<Json<InteractResponse>, String> {
    let ConnectRequest { host, port, input } = params.0;
    let stream = TcpStream::connect((host, port)).await.map_err(|e| e.to_string())?;
    *STATE.lock().unwrap() = Some(stream);
    interact(Parameters(InteractRequest { input })).await
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct InteractRequest {
    input: String,
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct InteractResponse {
    closed: bool,
    output: String,
}

/// Interacts with an open TCP connection in textual form.
///
/// The `input` parameter can be empty if interacting for output only. In the response, the `closed`
/// boolean indicates whether the peer closed the connection.
///
/// The tool will listen until some amount of inactivity or some fixed deadline, whichever happens
/// first. The tool will fail if the peer sends binary data that is not UTF-8.
#[rmcp::tool(name = "net_tcp_interact", annotations(destructive_hint = false))]
async fn _interact(_: Parameters<InteractRequest>) -> Result<Json<InteractResponse>, String> {
    // TODO(https://github.com/modelcontextprotocol/rust-sdk/issues/495): Remove when fixed.
    unreachable!()
}

#[allow(clippy::await_holding_lock)]
async fn interact(params: Parameters<InteractRequest>) -> Result<Json<InteractResponse>, String> {
    let InteractRequest { input } = params.0;
    let mut state = STATE.lock().unwrap();
    let Some(stream) = &mut *state else {
        return Err("no open connection".to_string());
    };
    if !input.is_empty() {
        stream.write_all(input.as_bytes()).await.map_err(|e| e.to_string())?;
    }
    const SIZE: usize = 1024;
    let mut output = vec![0; SIZE];
    let mut initialized = 0;
    let idle_time = *config::LOCAL_TOOL_IDLE_TIME.get().await.0;
    let timeout = tokio::time::sleep(*config::LOCAL_TOOL_TIMEOUT.get().await.0);
    tokio::pin!(timeout);
    let closed = loop {
        tokio::select! {
            biased;
            () = &mut timeout => break false,
            () = tokio::time::sleep(idle_time) => break false,
            len = stream.read(&mut output[initialized..]) => match len {
                Ok(0) => break true,
                Ok(len) => {
                    initialized += len;
                    output.resize(initialized + SIZE, 0);
                }
                Err(e) => return Err(e.to_string()),
            },
        }
    };
    output.truncate(initialized);
    let output = String::from_utf8(output).map_err(|e| e.to_string())?;
    Ok(Json(InteractResponse { closed, output }))
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct CloseRequest {}

/// Closes an open TCP connection.
#[rmcp::tool(name = "net_tcp_close", annotations(destructive_hint = false))]
async fn _close(_: Parameters<CloseRequest>) -> Result<Json<String>, String> {
    unreachable!()
}

#[allow(clippy::await_holding_lock)]
async fn close(params: Parameters<CloseRequest>) -> Result<Json<String>, String> {
    let CloseRequest {} = params.0;
    let Some(mut stream) = STATE.lock().unwrap().take() else {
        return Err("no open connection".to_string());
    };
    stream.shutdown().await.map_err(|e| e.to_string())?;
    Ok(Json("closed".to_string()))
}

static STATE: Mutex<Option<TcpStream>> = Mutex::new(None);
