// Copyright Kani Contributors
// SPDX-License-Identifier: Apache-2.0 OR MIT

use anyhow::{bail, Context, Result};
use kani_metadata::HarnessMetadata;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::process::Command;

use crate::call_cbmc::VerificationStatus;
use crate::session::KaniSession;

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

    fn wpst_status_from_file(
        &self,
        file: &Path,
        harness: &str,
        exec_stats: Option<PathBuf>,
    ) -> Result<VerificationStatus> {
        let mut args: Vec<OsString> =
            vec![self.kanillian_output_parser_py.clone().into(), file.into(), harness.into()];

        if let Some(stats) = &exec_stats {
            args.push("--stats".into());
            args.push(stats.clone().into_os_string());
        }

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
        gil_program: &Path,
        compile_stats: Option<PathBuf>,
        exec_stats: Option<PathBuf>,
    ) -> Result<VerificationStatus> {
        let mut args: Vec<OsString> = vec![
            WPST.into(),
            input.into(),
            "-o".into(),
            gil_program.clone().into(),
            "--harness".into(),
            harness.mangled_name.clone().into(),
            "-l".into(),
            "disabled".into(),
            "--json-ui".into(),
        ];
        if let Some(kstats_file) = &compile_stats {
            args.push("--kstats".into());
            args.push(kstats_file.clone().into_os_string());
        }

        let mut cmd = Command::new("kanillian");
        cmd.args(args);

        self.run_redirect(cmd, output)?;

        self.wpst_status_from_file(output, &harness.pretty_name, exec_stats)
    }
}
