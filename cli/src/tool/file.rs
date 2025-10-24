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

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

use data_encoding::HEXLOWER;
use rmcp::Json;
use rmcp::handler::server::wrapper::Parameters;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use crate::tool::Tools;

pub fn list(tools: &mut Tools) {
    tools.push(read_tool_attr(), read);
    tools.push(write_tool_attr(), write);
    tools.push(sha256_tool_attr(), sha256);
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct ReadRequest {
    path: String,
}

/// Reads a textual file.
#[rmcp::tool(name = "file_read")]
async fn read(params: Parameters<ReadRequest>) -> Result<Json<String>, String> {
    let ReadRequest { path } = params.0;
    let mut file = File::open(&path).await.map_err(|e| e.to_string())?;
    let mut content = String::new();
    let _: usize = file.read_to_string(&mut content).await.map_err(|e| e.to_string())?;
    Ok(Json(content))
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct WriteRequest {
    path: String,
    content: String,
    executable: Option<bool>,
}

/// Writes a textual file.
///
/// If the `executable` field is set to `true`, the file is made executable.
#[rmcp::tool(name = "file_write")]
async fn write(params: Parameters<WriteRequest>) -> Result<Json<String>, String> {
    let WriteRequest { path, content, executable } = params.0;
    let mut file = File::create(&path).await.map_err(|e| e.to_string())?;
    if executable.is_some_and(|x| x) {
        #[cfg(not(unix))]
        return Err("executable is only supported on unix".to_string());
        #[cfg(unix)]
        {
            let mut perms = file.metadata().await.map_err(|e| e.to_string())?.permissions();
            let mode = perms.mode();
            perms.set_mode(((mode & 0o222) >> 1) | mode);
            file.set_permissions(perms).await.map_err(|e| e.to_string())?;
        }
    }
    file.write_all(content.as_bytes()).await.map_err(|e| e.to_string())?;
    Ok(Json("done".to_string()))
}

#[derive(Serialize, Deserialize, JsonSchema)]
pub struct Sha256Request {
    path: String,
}

/// Computes the SHA256 of the content of a file given its path.
///
/// Returns the SHA256 in hexadecimal.
#[rmcp::tool(name = "file_sha256", annotations(read_only_hint = true))]
async fn sha256(params: Parameters<Sha256Request>) -> Result<Json<String>, String> {
    let content = tokio::fs::read(params.0.path).await.map_err(|e| e.to_string())?;
    let hash = Sha256::digest(&content);
    Ok(Json(HEXLOWER.encode(&hash)))
}
