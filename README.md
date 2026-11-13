# Rclone UI NATIVE Portable — independent Windows builder kit b1r3

**Purpose:** build the REAL `rclone/rclone-ui` Tauri/Rust GUI from a verified stable upstream Git tag as a directly executable Windows x64 `RcloneUI.exe`, containing its application-owned normal Tauri data under adjacent `Data/`. This is a **NATIVE-only** product, **not** PortableApps. No shared package-builder or custom NSIS installer is called. The only shared release action is `vhick/portable-release-publisher@v1.1.1`.

**b1r2 fix (retained):** `logs_117472741116.zip` exposed a Windows runner failure in
`scripts/prepare_deps.py` (`FileNotFoundError: [WinError 2]`) because Python
tried to spawn `npm` instead of the actual `npm.cmd` batch shim. The command
resolver now selects `npm.cmd` on Windows and `npm` elsewhere, without
using `shell=True`. The PowerShell build steps invoke `npm.cmd`/`npx.cmd`
explicitly, with a cheap PATH preflight and four regression tests. The
previous b1r2 run stopped during Tauri CLI version preflight; b1r3 has not yet
been run in hosted Windows CI. No native portability promises are inferred
from this fix.

**Evidence level:** project source and official Tauri 2.12.0 behavior inspected online; kit unit/static tests can run locally. The kit has NOT yet been built on hosted Windows, tested interactively on Windows, or used to publish a release. The workflow must succeed and then a real Windows acceptance check must pass before claiming runtime portability. New upstream releases may fail closed at a changed source anchor.

## Why source adaptation is essential

Upstream v3.7.5 uses Tauri 2.11.1, predating the application directory override introduced in Tauri 2.12.0. The adapter upgrades Rust tauri to 2.12.5, JavaScript @tauri-apps/api to 2.12.3, and @tauri-apps/cli to 2.12.4 (and updates tauri-build) and configures `AppDirectoriesOverride::Root("./Data")` **in the Rust app before the Tauri application is built or WebViews start**. Tauri resolves relative paths from the running EXE's folder. The separate headless Task Scheduler runner requires an explicit `current_exe()` data location patch; Windows headless runs cannot override this with stale `--data-dir` arguments. rclone child processes receive an EXE-adjacent `Data/rclone-cache/` and default `Data/rclone.conf` unless a specific config was supplied; this avoids rclone's ordinary LocalAppData cache and installed-system config search. App identifier and schedule folder are changed to avoid the installed GUI's identity and tasks. These are in-process source changes, **not** a launcher or environment harvesting.

Our portable build disables automatic Windows deep-link registration, upstream UI autostart plugin, upstream updater plugin, Sentry minidump telemetry, global rclone-process kill, user PATH modification and OS-wide config synchronization. Scheduling remains available only if the user registers tasks in the GUI. Registered Task Scheduler entries are intentional OS artifacts, and must be disabled or updated on folder moves. WebView2 system runtime and optional WinFsp are outside the portable distribution.

## GitHub Desktop setup (no local compiler)

1. On GitHub, create an **empty separate builder repository** such as `RcloneUI-Native-Portable-Builder`, not a fork of rclone/rclone-ui. Choose Public if you're happy to publish source and release files; Private if not.
2. Open GitHub Desktop > **File > Clone repository** > choose the new repository.
3. Extract **the complete contents** of this builder-kit ZIP into the repository's root. Hidden `.github/workflows/build-native.yml` must exist. Copy all kit files and directories, **not** the parent kit directory itself.
4. In GitHub Desktop, commit the new files and **Push origin**. No Git initialization or local tools needed.
5. On the GitHub repository website, select **Actions > Build Rclone UI Native Portable > Run workflow**. Set `upstream_version=latest` (or explicit `v3.7.5`) and `publish=true`. If running from a private repo, verify repository Actions settings and release visibility before publishing.
6. Read the Windows job logs: stable release; source SHA; patched source; locked dependencies; Windows compilation; cargo tests; direct headless invocation; independently validated ZIP; publisher **dry-run**; publisher **real upload**.
7. Under **Releases**, retrieve `RcloneUI-NativePortable-X.Y.Z-b1r3-win-x64.zip` and `SHA256SUMS.txt` (the pinned publisher generates checksums). Check SHA-256 before unpacking. The release tag records stable source SHA, patch hash and both resolved lock hashes.
8. Extract ZIP to a writable folder and **double-click `RcloneUI.exe` directly**. The `Data/` folder sits alongside. Do not run as Administrator without a specific need.
9. Complete `docs/ACCEPTANCE.md` on a real Windows desktop before trusting runtime portability or moving between drives.
10. To upgrade, **quit GUI and any associated work**, back up `Data/`, extract the replacement ZIP into a new empty folder, then copy `Data/` intact. For a downgrade, restore an older **matching Data snapshot**, not just an older EXE.

**Expected output layout:**

```text
RcloneUI-NativePortable/
  RcloneUI.exe                # genuine source-built Tauri GUI, no launcher
  Data/                       # application data, includes empty directories
  BUILD-IDENTITY.json
  README.txt
  README-VERIFY.txt
  LICENSES/
    UPSTREAM-LICENSE.txt
    THIRD_PARTY_MANIFEST.json
```

**No offline guarantee:** first-run app workflows may need to download a separate rclone binary into Data; no `rclone.exe` or WinFsp driver is falsely represented as bundled. The GUI itself is compiled from source and embeds frontend assets.

## Pipeline safeguards

- Only published **stable `vMAJOR.MINOR.PATCH`** GitHub Releases are accepted; beta, RC, cloud releases and drafts are discarded. Explicit stable version is checked against actual Releases.
- CI checks out exactly the tag's full SHA; it never silently builds main. Required upstream source anchors fail the build if changed.
- `npm ci` runs after regeneration of a resolved npm lockfile with exact Tauri CLI pin; Cargo updates required core packages and uses the resulting hashed Cargo lock for build and tests. All resolved identities are shipped with the application. These are identified dependency changes, not a bit-for-bit reproducible third-party build guaranteed across time.
- Before compiling, CI computes a release tag containing upstream commit, portable adapter fingerprint, Cargo lock fingerprint and npm lock fingerprint. It skips builds when a completed, publisher-managed release already exists. Unowned or incomplete tags BLOCK rather than silently overwrite.
- Compile is on GitHub-hosted `windows-latest`; only one job, on-demand. No interactive installers or paid runner required. Node/Rust/Edge WebView2 prerequisites on hosted runners are discovered through the normal toolchain.
- The published file must be a valid ZIP with an x64 PE binary and correct NATIVE structure. A short headless invocation is automatically tested. No GUI/tray/UI claim is made from CI alone.
- The pinned shared publisher is inspected against its real action.yml and resolved ref before use. It runs `dry-run: 'true'` first, then `dry-run: 'false'` when `publish=true`. Only ZIP is published. `keep-releases=3` and `prune=false`; no unrelated releases deleted.

## Important limitations

- **Upstream project may change:** adapters are intentionally version-sensitive. A changed source layout stops rather than silently producing a nonportable app.
- **Upstream Tauri update required:** version 2.12.5 must compile with the pinned upstream dependencies; this has not been proven here by a real Windows build.
- **Some UI features intentionally disabled:** updater, auto-login start, global process stop, PATH integration and config syncing. Their upstream UI buttons may fail/appear although safely blocked. Windows automatic protocol registration is also omitted.
- **Scheduled-task side effects:** user-created tasks intentionally live in Windows Task Scheduler (`\\RcloneUINativePortable\\`); startup reconciliation and stale task recovery require real Windows testing. A move makes task executable paths stale.
- **Installed-app coexistence:** distinct identifier/schedule namespace reduces collision risk, but notifications, platform single-instance behavior and Windows-managed caches require manual tests.
- **No claim of source-built rclone core:** app GUI is source-built; rclone engine is a separately managed external dependency. System WebView2/WinFsp remain optional OS runtime dependencies.
- **No guarantee that every plugin uses Tauri's standard app directory APIs:** host writes by third-party children must be observed in Windows testing. Do not call a build fully verified just because the portable root exists.

Refer to `docs/AUDIT.md`, `docs/FINDINGS-MATRIX.md`, `docs/VALIDATION-STATUS.md`, `docs/ACCEPTANCE.md`, `docs/TROUBLESHOOTING.md` and `docs/NATIVE-README.txt` for details.

## b1r3 fix — Tauri Rust / JavaScript core version consistency

`logs_117485897661.zip` showed that b1r2 successfully prepared locks and ran npm ci but
Tauri CLI refused compilation: `tauri (v2.12.5) : @tauri-apps/api (v2.11.0)`.
The upstream frontend API was not bumped when the backend was upgraded.
b1r3 pins `@tauri-apps/api` to verified stable 2.12.3 (matching the Rust 2.12 minor),
regenerates the npm lock, and adds checks against actual npm/Cargo locks in dependency
preparation and actual installed npm files before compilation. Six new tests cover
API version patching, invalid lockfiles and a valid lockfile fixture.

This corrects the recorded mismatch but does NOT prove source compilation or runtime
portability; the next GitHub Windows job must determine that.
