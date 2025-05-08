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

use std::fmt::Display;

use clap::Parser as _;
use env_logger::{Env, init_from_env};

use crate::cli::{Cli, FLAGS};

macro_rules! fail {
    ($($x:tt)*) => {{
        use colored::Colorize;
        println!("{}: {}", "Error".bold().red(), format!($($x)*));
        std::process::exit(1);
    }};
}

mod cli;
mod sdk;

#[tokio::main]
async fn main() {
    let Cli { flags, action } = Cli::parse();
    FLAGS.set(flags);
    init_from_env(Env::new().default_filter_or(&FLAGS.log_level));
    action.run().await
}

fn or_fail<T, E: Display>(x: Result<T, E>) -> T {
    match x {
        Ok(x) => x,
        Err(e) => fail!("{e}"),
    }
}
