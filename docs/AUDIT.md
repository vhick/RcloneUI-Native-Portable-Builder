# Project-specific source audit and threat model

Observed stable release: rclone/rclone-ui v3.7.5, upstream release page abbreviated commit `453cc0c`, published September 18, 2026. The workflow fetches and records the **full commit** for the requested stable tag at build time, not a guessed SHA. The subsequent v4.0.0-beta releases are excluded by the `vMAJOR.MINOR.PATCH` stable-only policy. The source is Apache-2.0. Rust Tauri 2, npm/TypeScript/Vite and both `package-lock.json` and `src-tauri/Cargo.lock` are used. Publisher v1.1.1 action.yml and publication script were reviewed; the publisher supports ZIP release files and generates its own SHA256SUMS.txt. NATIVE mode has no installer engine.

| Finding | Evidence | Path or entry | Owner | NATIVE fix | Data safety / functionality cost | Verification |
|---|---|---|---|---|---|---|
| Tauri app data and stores | `scheduler/storeread.rs`, `zookeeper.rs` source | Roaming/Local `com.rclone.ui`, managed rclone versions, host stores | Tauri and app | Source-driven Tauri 2.12 AppDirectoriesOverride => EXE/Data; patch headless runner | Local data isolated; new Tauri dependency must be compiled/tested | SOURCE-INSPECTED; runtime NOT VERIFIED |
| WebView2 profiles, log, cache | Tauri 2.12 documentation | Tauri standard app-local/cache/log paths | Tauri/WebView2 | Tauri root override before Builder.build | OS-managed caches still possible; no global APPDATA change | SOURCE-INSPECTED framework documentation; runtime NOT VERIFIED |
| rclone child cache/default config | `zookeeper.rs:exec_blocking,spawn_rclone`, `scheduler/runner.rs`; rclone official docs | `%LOCALAPPDATA%/rclone` default cache; system default config | rclone child processes | Source-insert `RCLONE_CACHE_DIR=Data/rclone-cache` for GUI and scheduled children, default config `Data/rclone.conf` unless app explicitly selects one | No global environment changes; external `--cache-dir` arguments remain user-controlled | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Headless scheduling | `src/main.rs`, `scheduler/storeread.rs` | Task Scheduler command and app data paths | App + Windows | current_exe() based Data for headless (ignore user-supplied overrides on Windows), isolated `RcloneUINativePortable` task folder | Intentional explicit OS tasks persist after closure and need re-registration on relocation | SOURCE-INSPECTED; execution NOT VERIFIED |
| System PATH edits | `zookeeper.rs:set_rclone_path_integration` | HKCU Environment Path | App | Block mutation, keep managed engine paths | PATH button disabled | SOURCE-INSPECTED; runtime NOT VERIFIED |
| System rclone config sync | `zookeeper.rs:set_config_sync`, `system_config_path` | user `.config/rclone/rclone.conf`, symlink | App | Block mutation | Config-sync button disabled; installed config protected | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Global rclone kill command | `lib.rs:stop_rclone_processes` | all `rclone.exe` PIDs | App | Replace with hard error; keep owned-daemon stop | Global stop control disabled, avoids killing installed user jobs | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Deep link registration | `lib.rs:setup`, `tauri.conf.json` | `rclone://` default handler | App + Windows | Remove Windows register_all; remove scheme in portable build config | Deep-link open-from-browser unavailable | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Updater/self-replacement | `lib.rs`, Tauri plugin and bundled config | app binary/updater artifacts | Plugin | Remove update plugin and artifacts; ZIP replacement | Manual updates instead | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Auto-start | `lib.rs`, tauri-plugin-autostart | HKCU Run / login shell | Plugin | Do not load autostart plugin | Autostart UI unavailable; no automatic login entry | SOURCE-INSPECTED; runtime NOT VERIFIED |
| Telemetry/minidumps | `lib.rs` Sentry init | framework minidump locations | Third party | Remove native Sentry initialization and plugin | Native crash telemetry absent; JS analytics dependencies not fully audited | SOURCE-INSPECTED; runtime NOT VERIFIED |
| rclone binary downloads | `zookeeper.rs` | Tauri app local `rclone-versions/` | Application | Tauri local data redirects managed version storage | First-run may need internet; no offline engine in ZIP | SOURCE-INSPECTED; runtime NOT VERIFIED |
| WinFsp | rclone official install docs | system-installed filesystem driver | External driver | Never install silently | Mounts require explicit user installation | DOCUMENTED external dependency |
| Windows shell notifications/caches | Tauri plugin, Windows-managed state | variable OS paths | Framework/OS | Distinct identifier, disable auto protocol registration | Notification compatibility and persistent OS caches remain to test | NOT YET VERIFIED |
| Absolute configured external paths | rclone config and scheduler | user-selected folders/drives | App/user | No automatic rewriting of external paths | User must repair after drive relocation | SOURCE-INSPECTED risk; runtime NOT VERIFIED |

**Why not set global APPDATA:** it may affect child processes and does not necessarily redirect Windows Known Folder APIs. Tauri 2.12 runtime config override is scoped to Tauri's app-owned storage. Other child tools are audited/blocked individually when identified.

**Explicit limitations:** Neither a successful build nor static PE/ZIP verification demonstrates completeness of storage containment. Host-only OS caches and user-approved scheduled tasks are documented exceptions. Exact side effects of all Tauri dependency/JavaScript plugins and rclone children need ProcMon observations on Windows. `rclone` itself is not rebuilt from source by this kit; the upstream GUI uses its existing engine downloader.

**Official source locations:**
- https://github.com/rclone/rclone-ui/releases/tag/v3.7.5
- https://raw.githubusercontent.com/rclone/rclone-ui/v3.7.5/src-tauri/src/lib.rs
- https://raw.githubusercontent.com/rclone/rclone-ui/v3.7.5/src-tauri/src/zookeeper.rs
- https://raw.githubusercontent.com/rclone/rclone-ui/v3.7.5/src-tauri/src/scheduler/storeread.rs
- https://raw.githubusercontent.com/rclone/rclone-ui/v3.7.5/src-tauri/src/scheduler/schtasks.rs
- https://v2.tauri.app/release/tauri/v2.12.0/
- https://v2.tauri.app/reference/config/
- https://raw.githubusercontent.com/vhick/portable-release-publisher/v1.1.1/action.yml
- https://raw.githubusercontent.com/vhick/portable-release-publisher/v1.1.1/scripts/publish.py
