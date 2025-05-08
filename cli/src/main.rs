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

macro_rules! fail {
    ($($x:tt)*) => {{
        use colored::Colorize;
        println!("{}: {}", "Error".bold().red(), format!($($x)*));
        std::process::exit(1);
    }};
}

mod cli;
mod config;
mod sdk;
mod util;

#[tokio::main]
async fn main() {
    env_logger::init();
    <cli::Action as clap::Parser>::parse().run().await
}

fn or_fail<T, E: std::fmt::Display>(x: Result<T, E>) -> T {
    match x {
        Ok(x) => x,
        Err(e) => fail!("{e}"),
    }
}

fn try_to<T, E: std::fmt::Display>(f: &str, x: Result<T, E>) -> T {
    match x {
        Ok(x) => x,
        Err(e) => fail!("Failed to {f}: {e}"),
    }
}
