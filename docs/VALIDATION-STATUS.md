# b1r3 implementation and evidence status

This file records the **kit's creation-time** evidence. Build-time steps change their state only after a real hosted Windows workflow has run. The text below is intentionally not rewritten automatically into a claim of successful GUI portability.

| Check | Kit-creation evidence | CI goal | User Windows acceptance |
|---|---|---|---|
| Stable upstream release, official source locations | SOURCE-INSPECTED (v3.7.5) | Resolve published stable tag and full Git SHA | N/A |
| Publisher v1.1.1 inputs and implementation | SOURCE-INSPECTED (action.yml, publish.py) | Revalidate pinned action tag before calling action | N/A |
| Script Python syntax | STATIC-VALIDATED (`compileall`) | Python scripts execute | N/A |
| Release sorting and safeguards | STATIC-VALIDATED (unit tests) | Unit tests pass | N/A |
| Workflow YAML parsing | STATIC-VALIDATED (PyYAML local parser) | GitHub Actions loads and dispatches | N/A |
| Exact upstream source patches | SOURCE-INSPECTED design; applied to checkout only on CI | Fail-closed source adapter | Native app must run |
| Full Windows executable compilation | NOT YET VERIFIED | WINDOWS-COMPILED | N/A |
| Headless direct exe CLI | NOT YET VERIFIED | AUTOMATED-RUNTIME-TESTED | Confirm from non-app CWD |
| Direct interactive GUI and tray | NOT YET VERIFIED | Cannot be inferred | MANUAL-WINDOWS-TESTED |
| Local Data and WebView2 storage | NOT YET VERIFIED | Static source assertion only | MANUAL-WINDOWS-TESTED |
| Child rclone and scheduled tasks | NOT YET VERIFIED | cargo tests and headless only | MANUAL-WINDOWS-TESTED |
| Shell registries/OS notifications | NOT YET VERIFIED | None | MANUAL-WINDOWS-TESTED |
| Windows startup/autostart | NOT YET VERIFIED | Blocked by source adapter | MANUAL-WINDOWS-TESTED |
| Native ZIP generation and checksum | NOT YET VERIFIED | STATIC-VALIDATED once built | User verifies release SHA |
| Installer | NOT APPLICABLE (NATIVE ONLY) | None | None |
| Shared publisher dry-run & release | NOT YET VERIFIED | Publisher dry run then live upload | Check published release in builder repo |
| User confirmed functioning | NOT YET VERIFIED | N/A | USER-CONFIRMED after actual use |

No real RcloneUI.exe or native application ZIP is included in the kit. The kit builds them on Windows; upstream source and all dependencies are fetched unattended from their official locations. In this runtime, GitHub DNS resolution was unavailable, and Windows compilation/execution was not possible.

## b1r2 Windows npm shim repair

User-provided GitHub Actions log `logs_117472741116.zip` confirmed b1r1's
source and patching steps passed, then Step 10 failed under Python 3.13 on
Windows before Cargo compilation because an extensionless `npm` command was
not resolvable by `subprocess.run` (`WinError 2`). The b1r2 adaptation uses
`npm.cmd`, includes four mock-based unit tests, and invokes both npm and npx
using their Windows `.cmd` names from PowerShell. These local regression
tests are **STATIC-VALIDATED**, not Windows execution evidence.

**Remaining:** b1r3 must pass the entire hosted Windows job; Rust/Tauri
compilation, `RcloneUI.exe` functionality, local-data isolation, interactive
GUI and publisher execution remain NOT YET VERIFIED.

## b1r3 dependency mismatch correction

Observed in GitHub Actions logs `logs_117485897661.zip`: b1r2 dependency
lock refresh, source validation and npm ci succeeded; Tauri CLI refused to
build because Rust tauri 2.12.5 did not match JS API 2.11.0.
b1r3 patches the npm API to 2.12.3 and adds a locked-resolution preflight.
Local regression tests validate the correction logic with synthetic manifests;
**Windows application compilation and runtime behavior remain NOT YET VERIFIED.**
