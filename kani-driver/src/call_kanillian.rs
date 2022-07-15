// Copyright Kani Contributors
// SPDX-License-Identifier: Apache-2.0 OR MIT

use anyhow::{bail, Context, Result};
use kani_metadata::HarnessMetadata;

use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::process::Command;

use crate::call_cbmc::VerificationStatus;
use crate::session::KaniSession;

// #[derive(Debug)]
// pub enum KanillianWPSTStatus {
//     Success,
//     AssertFailed,
//     UnhandledAtCompilation(String),
//     UnhandledAtExec(String),
//     OtherFailure,
// }

// impl KanillianWPSTStatus {
//     fn parse(str: &str) -> Self {
//         match str {
//             "Success" => Self::Success,
//             "AssertFailed" => Self::AssertFailed,
//             _ => match str.strip_prefix("UnhandledAtExec::") {
//                 Some(feature) => Self::UnhandledAtExec(feature.to_owned()),
//                 None => Self::OtherFailure,
//             },
//         }
//     }
// }

const WPST: &str = "wpst";

impl KaniSession {
    fn run_terminal_for_kanillian_parser(&self, mut cmd: Command) -> Result<Option<i32>> {
        if self.args.quiet {
            cmd.stdout(std::process::Stdio::null());
            cmd.stderr(std::process::Stdio::null());
        }
        if self.args.verbose || self.args.dry_run {
            println!("{}", crate::util::render_command(&cmd).to_string_lossy());
            if self.args.dry_run {
                // Short circuit
                return Ok(None);
            }
        }
        cmd.status()
            .context(format!("Failed to invoke {}", cmd.get_program().to_string_lossy()))
            .map(|x| x.code())
    }

    fn wpst_status_from_file(&self, file: &Path, harness: &str) -> Result<VerificationStatus> {
        let args: Vec<OsString> =
            vec![self.kanillian_output_parser_py.clone().into(), file.into(), harness.into()];

        let mut cmd = Command::new("python3");
        cmd.args(args);

        let code = self.run_terminal_for_kanillian_parser(cmd)?;

        match code {
            Some(1) => {
                println!("PYTHON ERROR");
                bail!("There was an error while reading the Kanillian output")
            }
            Some(0) => Ok(VerificationStatus::Success),
            _ => Ok(VerificationStatus::Failure),
        }
    }
    // let stdout = std::str::from_utf8(&output.stdout)?;
    // let res = stdout.lines().map(KanillianWPSTStatus::parse).collect();

    pub fn call_kanillian_wpst(
        &self,
        input: &PathBuf,
        harness: &HarnessMetadata,
        output: &Path,
        kstats_file: Option<&Path>,
    ) -> Result<VerificationStatus> {
        let mut args: Vec<OsString> = vec![
            WPST.into(),
            input.into(),
            "--harness".into(),
            harness.mangled_name.clone().into(),
            "-l".into(),
            "disabled".into(),
            "--json-ui".into(),
        ];
        if let Some(kstats_file) = kstats_file {
            args.push("--kstats".into());
            args.push(kstats_file.to_owned().into_os_string());
        }

        let mut cmd = Command::new("kanillian");
        cmd.args(args);

        self.run_redirect(cmd, output)?;

        self.wpst_status_from_file(output, &harness.pretty_name)
    }
}
