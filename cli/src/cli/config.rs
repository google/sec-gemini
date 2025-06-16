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

use colored::Colorize as _;

use crate::config::{self, Name};

#[derive(clap::Args)]
pub struct Action {
    #[command(subcommand)]
    command: Command,
}

#[derive(clap::Subcommand)]
enum Command {
    /// Lists all configuration files with their value.
    List,

    /// Reads a specific configuration file.
    Read {
        /// The name of the configuration file.
        name: Name,
    },

    /// Writes a specific configuration file.
    Write {
        /// The name of the configuration file.
        name: Name,

        /// The value of the configuration file.
        value: String,
    },

    /// Deletes a specific configuration file.
    Delete {
        /// The name of the configuration file.
        name: Name,
    },
}

impl Action {
    pub async fn run(self) {
        match self.command {
            Command::List => {
                let mut table = Vec::new();
                let mut width = 0;
                for config in config::list() {
                    if let Some(value) = config.get_file().await {
                        let name = config.name();
                        width = std::cmp::max(width, name.len());
                        table.push((name, value));
                    }
                }
                for (name, value) in table {
                    println!("{:>width$}: {}", name.purple(), value.green());
                }
            }
            Command::Read { name } => match name.config().get_file().await {
                None => println!("There is no value."),
                Some(value) => println!("The value is: {value}"),
            },
            Command::Write { name, value } => {
                let config = name.config();
                if let Some(error) = config.validate(&value) {
                    return user_error!("invalid value: {error}");
                }
                config.write(value).await
            }
            Command::Delete { name } => name.config().delete().await,
        }
    }
}
