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

use std::io::ErrorKind;
use std::ops::Deref;
use std::path::PathBuf;

use dialoguer::Input;
use directories::ProjectDirs;

use crate::{fail_str, try_to};

/// A configurable value.
pub struct Config(ConfigImpl);

pub struct Desc {
    /// The name of the config file.
    config: &'static str,
    /// The name to use in the terminal prompt.
    prompt: &'static str,
    /// The name of the flag.
    flag: &'static str,
    /// The name of the environment variable (if any).
    env: Option<&'static str>,
}

pub static API_KEY: Desc = Desc {
    config: "api-key",
    prompt: "API key",
    flag: "--api-key",
    env: Some("SEC_GEMINI_API_KEY"),
};

impl Deref for Config {
    type Target = str;

    fn deref(&self) -> &Self::Target {
        match &self.0 {
            ConfigImpl::Unknown { .. } => unreachable!(),
            ConfigImpl::Known { value, .. } => value,
            ConfigImpl::Frozen { value } => value,
        }
    }
}

impl Config {
    /// Creates an unknown value (must be forced before deref).
    pub const fn unknown(desc: &'static Desc) -> Self {
        Config(ConfigImpl::Unknown { desc })
    }

    /// Creates a frozen value (persist is ignored).
    pub fn frozen(value: String) -> Self {
        Config(ConfigImpl::Frozen { value })
    }

    /// Makes sure the value exists (reading from config or terminal if needed).
    ///
    /// The config file is ignored with `bypass` and the value is read from the terminal.
    pub fn force(&mut self, bypass: bool) {
        if let ConfigImpl::Unknown { desc } = self.0 {
            self.0 = read_value(desc, bypass);
        }
    }

    /// Resets the value to unknown if read from config (does nothing otherwise).
    ///
    /// Returns whether the value was reset.
    pub fn reset(&mut self) -> bool {
        if let ConfigImpl::Known { config: true, desc, .. } = &self.0 {
            self.0 = ConfigImpl::Unknown { desc };
            true
        } else {
            false
        }
    }

    /// Persists the config of a known value read from terminal (does nothing otherwise).
    pub fn persist(&self) {
        if let ConfigImpl::Known { value, path, config: false, desc } = &self.0 {
            let prompt = desc.prompt;
            log::info!("Writing {prompt} config file.");
            let config_dir = path.parent().unwrap();
            try_to("create Sec-Gemini config directory", std::fs::create_dir_all(config_dir));
            try_to(&format!("write {prompt} config file"), std::fs::write(path, value.as_bytes()));
        }
    }
}

enum ConfigImpl {
    /// The value is unknown.
    Unknown {
        /// The description of the value.
        desc: &'static Desc,
    },
    /// The value is known.
    Known {
        /// The value read from the config file or from the terminal.
        value: String,
        /// The path of the config file.
        path: PathBuf,
        /// Whether the value was read from the config file.
        config: bool,
        /// The description of the value.
        desc: &'static Desc,
    },
    /// The value is known and frozen.
    ///
    /// The config file can't be modified.
    Frozen {
        /// The value read from the command line or from the environment.
        value: String,
    },
}

struct DescInstr(&'static Desc);

impl std::fmt::Display for DescInstr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Set the {} flag", self.0.flag)?;
        match self.0.env {
            Some(x) => write!(f, " or the {x} environment variable."),
            None => write!(f, "."),
        }
    }
}

impl Desc {
    fn instr(&'static self) -> DescInstr {
        DescInstr(self)
    }
}

fn read_value(desc: &'static Desc, bypass: bool) -> ConfigImpl {
    let Desc { config, prompt, .. } = desc;
    let instr = desc.instr();
    let Some(dirs) = ProjectDirs::from("", "Google", "Sec-Gemini") else {
        fail_str("failed to find Sec-Gemini config directiory", None, Some(&instr));
    };
    let config_dir = dirs.config_dir();
    let path = config_dir.join(config);
    if !bypass {
        log::debug!("Reading {prompt} from {}.", path.display());
        match std::fs::read(&path) {
            Ok(x) => match String::from_utf8(x) {
                Ok(value) => return ConfigImpl::Known { value, path, config: true, desc },
                Err(_) => {
                    log::warn!("{prompt} config file is not UTF-8. Removing it.");
                    try_to(&format!("remove {prompt} config file"), std::fs::remove_file(&path));
                }
            },
            Err(e) if e.kind() == ErrorKind::NotFound => (),
            Err(e) => fail!("failed to read {prompt} config file"; &e),
        }
    }
    if !console::user_attended() {
        fail!("Sec-Gemini {prompt} is not set" => &instr);
    }
    log::debug!("Reading {prompt} from terminal.");
    let value: String = try_to(
        &format!("read {prompt} from terminal"),
        Input::new().with_prompt(format!("Enter your Sec-Gemini {prompt}")).interact_text(),
    );
    ConfigImpl::Known { value, path, config: false, desc }
}
