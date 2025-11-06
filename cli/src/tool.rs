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

use std::collections::BTreeMap;
use std::pin::Pin;

use rmcp::Json;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::JsonObject;
use serde::Serialize;
use serde::de::DeserializeOwned;
use serde_json::Value;

mod exec;
mod file;
mod net;

pub type CallOutput<R> = Result<Json<R>, String>;
pub type CallResult<R> = Pin<Box<dyn Future<Output = CallOutput<R>>>>;

pub struct Tools {
    tools: BTreeMap<String, Tool>,
}

pub struct Tool {
    pub desc: String,
    pub input: JsonObject,
    pub reorder: Box<dyn Fn(Value) -> CallResult<Value> + Send + Sync>,
    pub call: Box<dyn Fn(Value) -> CallResult<Value> + Send + Sync>,
    pub effect: Effect,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Effect {
    ReadOnly,
    Mutating,
    Destructive,
}

pub struct Enable(Vec<(bool, String)>);

impl Enable {
    pub async fn parse() -> Self {
        let (list, _) = crate::config::LOCAL_TOOL_ENABLE.get().await;
        Enable(
            list.split([',', ' '])
                .map(|x| match x.strip_prefix("!") {
                    Some(x) => (false, x.to_string()),
                    None => (true, x.to_string()),
                })
                .collect(),
        )
    }

    pub fn check(&self, name: &str) -> bool {
        let mut enabled = true;
        for (enable, prefix) in &self.0 {
            if name.starts_with(prefix) {
                enabled = *enable;
            }
        }
        enabled
    }
}

impl Tools {
    pub fn list() -> Tools {
        let mut tools = Tools { tools: BTreeMap::new() };
        exec::list(&mut tools);
        file::list(&mut tools);
        net::list(&mut tools);
        tools
    }

    pub fn iter(&self) -> impl Iterator<Item = (&str, &Tool)> {
        self.tools.iter().map(|(x, y)| (x.as_str(), y))
    }

    pub fn get(&self, name: &str) -> Option<&Tool> {
        self.tools.get(name)
    }

    pub fn retain(&mut self, f: impl Fn(&str) -> bool) {
        self.tools.retain(|x, _| f(x));
    }

    fn push<P, R, F>(&mut self, tool: rmcp::model::Tool, call: fn(Parameters<P>) -> F)
    where
        P: Serialize + DeserializeOwned + 'static,
        R: Serialize,
        F: Future<Output = CallOutput<R>> + 'static,
    {
        let name = tool.name.to_string();
        let desc = tool.description.map_or(String::new(), |x| x.to_string());
        let input = (*tool.input_schema).clone();
        let reorder = Box::new(move |x| {
            Box::pin(async move {
                let x: P = serde_json::from_value(x).map_err(|e| e.to_string())?;
                Ok(Json(serde_json::to_value(x).map_err(|e| e.to_string())?))
            }) as CallResult<Value>
        });
        let call = Box::new(move |x| {
            Box::pin(async move {
                let x = serde_json::from_value(x).map_err(|e| e.to_string())?;
                let Json(r) = call(Parameters(x)).await?;
                Ok(Json(serde_json::to_value(r).map_err(|e| e.to_string())?))
            }) as CallResult<Value>
        });
        let annotations = tool.annotations.unwrap_or_default();
        let effect =
            match (annotations.read_only_hint.unwrap_or(false), annotations.is_destructive()) {
                (true, _) => Effect::ReadOnly,
                (false, false) => Effect::Mutating,
                (false, true) => Effect::Destructive,
            };
        let tool = Tool { desc, input, reorder, call, effect };
        assert!(self.tools.insert(name, tool).is_none());
    }
}
