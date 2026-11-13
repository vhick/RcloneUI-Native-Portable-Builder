# b1r1 implementation and evidence status

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
