# Troubleshooting

**`patch_source.py`: expected source anchor not found.** The selected upstream release changed. Do not delete the safety check or build `main`. Compare the tagged new source with the adapter; update it only after a fresh audit. Choose explicit v3.7.5 to test the known source revision.

**Cargo cannot resolve Tauri 2.12.5 or tauri-build 2.7.4.** Upstream's pinned Git dependency (`fix-path-env`) or a plugin may not support the newer version. Check the Cargo error; revise dependency compatibility only after verifying a compatible Tauri version >=2.12.0. Do not fall back to 2.11.1: that silently loses native storage override.

**`FileNotFoundError: [WinError 2]` in `prepare_deps.py` (b1r1 regression).**
The Windows Node.js runner uses `npm.cmd`, not an extensionless executable.
Upgrade all builder files to b1r2; do not copy only the Python script.
The b1r2 `Verify Windows Node.js command shims` step checks the PATH and
`prepare_deps.py` invokes `npm.cmd` explicitly without a shell. If the shim
preflight fails, inspect `actions/setup-node` and the runner PATH before trying
`npm` or changing execution policies.

**`npm ci` fails.** Inspect the lock refresh phase, npm code-page problems and network availability. Do not substitute `npm install` during the compile step; `npm ci` must build from the refreshed locked tree.

**`RcloneUI.exe` absent.** Inspect actual Cargo/CLI output path (`src-tauri/target/x86_64-pc-windows-msvc/release/`). The adapter sets an explicit `[[bin]]` name and disables implicit auto binaries. CI stops on missing executable rather than shipping a dummy file.

**GUI opens but no cloud backends work.** The UI relies on a separately managed `rclone.exe`, which may need an in-app version download. On Windows, mounting requires installed WinFsp. Verify app's local Data/rclone-versions and config selection; do not blindly switch it to an installed user's system config.

**Scheduled jobs don't work after moving the folder.** Their Windows Task Scheduler definitions contain absolute executable paths and stored data-dir flags. Disable/remove only your portable namespace tasks using the app, then explicitly re-register once stable. Do not delete other apps' Task Scheduler entries.

**Updater/PATH/config-sync/startup button fails.** Expected portable-build safety restriction. Update by replacing binaries while preserving the local Data folder. Disable old scheduled tasks before changing drive paths. Do not patch out the safety guards to make these controls green.

**Windows antivirus warns about unsigned EXE.** This kit does not sign binaries, register a certificate, or attempt bypass. Verify GitHub Actions provenance and SHA256SUMS, investigate the alert and avoid disabling security protections.

**WebView2 missing or browser data outside Data.** Runtime must be installed on the host. Test with ProcMon or equivalent normal diagnostic and inspect process-specific file operations; if child framework writes outside Data, stop distribution and patch the precise source/framework data-directory call. Never implement broad host cleanup.

**Publisher action refuses to publish.** Ensure `contents:write`, selected tag prefix, immutable identity, valid ZIP, and repository action settings. It intentionally refuses unrelated tagged releases and uses no PAT.
