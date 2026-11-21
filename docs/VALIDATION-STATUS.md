# b1r4 implementation and evidence status

This file records the **kit's creation-time** evidence. Build-time steps change their state only after a real hosted Windows workflow has run. The text below is intentionally not rewritten automatically into a claim of successful GUI portability.

| Check | Kit-creation evidence | CI goal | User Windows acceptance |
|---|---|---|---|
| Stable upstream release, official source locations | SOURCE-INSPECTED (v3.7.5 baseline and v3.7.7 failure fixture) | Resolve published stable tag and full Git SHA | N/A |
| Publisher v1.1.1 inputs and implementation | SOURCE-INSPECTED (action.yml, publish.py) | Revalidate pinned action tag before calling action | N/A |
| Script Python syntax | STATIC-VALIDATED (`compileall`) | Python scripts execute | N/A |
| Release sorting and safeguards | STATIC-VALIDATED (unit tests) | Unit tests pass | N/A |
| Workflow YAML parsing | STATIC-VALIDATED (PyYAML local parser) | GitHub Actions loads and dispatches | N/A |
| Exact upstream source patches | SOURCE-INSPECTED design; applied to checkout only on CI | Fail-closed source adapter | Native app must run |
| Full Windows executable compilation | WINDOWS-COMPILED v3.7.7 b1r3 according to supplied Nov 21 Actions log; b1r4 NOT YET VERIFIED | WINDOWS-COMPILED | N/A |
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

**Remaining:** b1r4 must pass the full hosted Windows job. The provided v3.7.7
log confirms compilation but not full cargo tests, headless smoke, packaging or publication.
Real local-data isolation and interactive GUI remain incompletely verified.

## b1r3 dependency mismatch correction

Observed in GitHub Actions logs `logs_117485897661.zip`: b1r2 dependency
lock refresh, source validation and npm ci succeeded; Tauri CLI refused to
build because Rust tauri 2.12.5 did not match JS API 2.11.0.
b1r3 patches the npm API to 2.12.3 and adds a locked-resolution preflight.
Local regression tests validate the correction logic with synthetic manifests;
**b1r3 v3.7.7 compilation is confirmed by the user-provided log; b1r4 execution remains NOT YET VERIFIED.**

## b1r4 cross-platform upstream ZIP-test fixture fix

`logs_121440054520.zip`: source v3.7.7 (`90b7a7f3254df95bcb82bdfedd44fe700a17d76b`),
Tauri Windows compilation succeeded; `cargo test --locked` ran 54 tests, 53
passed and `zookeeper::tests::unzip_extracts_files_and_modes` failed with
`Option::unwrap() on None`. Exact upstream source shows the fixture contained
`rclone-v1-osx/rclone`, while `find_binary()` expects `bin_name()` (`rclone.exe`
on Windows). b1r4 changes **only this known test fixture** to use `bin_name()`.

- SOURCE-INSPECTED: upstream v3.7.7 release and `zookeeper.rs` test and finder.
- STATIC-VALIDATED: 22 local Python kit tests including six compatibility cases,
  Python compile and YAML structure / ZIP archive verification.
- WINDOWS-COMPILED: the upstream-derived b1r3 application in the supplied log.
- NOT YET VERIFIED: b1r4 Windows compilation, full Rust test pass, headless smoke,
  native ZIP production, release publication, and complete runtime data containment.

The source adapter fails safely if changed production API anchors are
unrecognized; `compat_tests.py` is not an unconditional suppress-errors mechanism.
