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

use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

use clap::{CommandFactory, ValueHint};
use clap_complete::Shell;

#[derive(clap::Args)]
pub struct Action {
    /// Generates a completion file for this shell (tries to guess by default).
    shell: Option<Shell>,

    /// Where to generate the completion file.
    #[arg(long, default_value = "-", value_hint = ValueHint::FilePath)]
    output: PathBuf,
}

impl Action {
    pub async fn run(self) {
        let shell = try_to!("guess a shell", self.shell.or_else(Shell::from_env));
        let mut cmd = crate::cli::Action::command();
        let mut output: Box<dyn Write> = if self.output == Path::new("-") {
            Box::new(std::io::stdout())
        } else {
            let name = self.output.display();
            let parent = try_to!("get parent directory of {name}", self.output.parent());
            try_to!("create parent directories for {name}", std::fs::create_dir_all(parent));
            Box::new(try_to!("create output file {name}", File::create(&self.output)))
        };
        let name = cmd.get_name().to_string();
        clap_complete::generate(shell, &mut cmd, name, &mut output);
    }
}
