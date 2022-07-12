// Copyright Kani Contributors
// SPDX-License-Identifier: Apache-2.0 OR MIT

use anyhow::Result;

use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::process::Command;

use crate::session::KaniSession;

const WPST: &str = "wpst";

impl KaniSession {
    pub fn call_kanillian(
        &self,
        input: &PathBuf,
        harness: String,
        output: Option<&Path>,
        kstats_file: Option<&Path>,
    ) -> Result<()> {
        let mut args: Vec<OsString> = vec![
            WPST.into(),
            input.into(),
            "--harness".into(),
            harness.into(),
            "-l".into(),
            "disabled".into(),
        ];
        if let Some(output_path) = output {
            args.push("-o".into());
            args.push(output_path.to_owned().into_os_string());
        }
        if let Some(kstats_file) = kstats_file {
            args.push("--kstats".into());
            args.push(kstats_file.to_owned().into_os_string());
        }

        let mut cmd = Command::new("kanillian");
        cmd.args(args);

        self.run_suppress(cmd)?;
        Ok(())
    }
}
