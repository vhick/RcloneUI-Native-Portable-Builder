# Manual Windows acceptance (REQUIRED before claiming fully portable)

These checks **are not automated by hosted CI** and are **not marked passed**.

Use an isolated Windows 10/11 account or disposable VM, ordinary user permissions, Microsoft Edge WebView2 Runtime present, and optionally WinFsp installed only if mount tests need it. Make a restore point or VM snapshot. Use ProcMon process filters targeting `RcloneUI.exe` and its rclone child, not global delete scripts.

1. Extract to `C:\Temp\Native Test Ω\RcloneUI-NativePortable\`, keep an existing installed Rclone UI/rclone profile intact. Launch **RcloneUI.exe itself**, no script. Confirm GUI/tray opens and can exit completely.
2. Change a preference, close through the tray (not only window close), relaunch from a different working directory. Confirm preferences persist in `Data/`. Inspect new nested empty folders too.
3. Use a test remote with disposable credentials and the managed engine downloader. Confirm stored rclone versions, tasks/history, caches (`Data/rclone-cache`) and config files under `Data/`. Confirm subprocess rclone `config paths` shows the cache in Data and does not pick up installed rclone configuration by default. Verify config encryption portability separately where relevant.
4. Inspect per-process writes to `%APPDATA%`, `%LOCALAPPDATA%`, LocalLow, `%PROGRAMDATA%`, `%USERPROFILE%`, `%TEMP%`, Windows registry and shell. Distinguish temporary files, Windows-managed caches and genuine application persistent state. Record exact paths and owner. Do **not** delete unknown paths.
5. Open the GUI twice. Check there is only one intended portable GUI instance and that an already installed Rclone UI remains usable. Confirm no conflicting installed-app notification identity or protocol takeover.
6. Inspect HKCU PATH, `HKCU\Software\Classes`, Windows default handlers, start-menu/startup shortcuts and Task Scheduler BEFORE and AFTER a first run. There should be no automatic PATH change or protocol owner registration. Check the portable restrictions on updater/PATH/config sync/global rclone kill are respected.
7. Close tray/window and verify managed rclone daemon ends without killing an unrelated installed or CLI rclone job.
8. Register one test scheduled job from the GUI ONLY after verifying its exact target. It should create a task under `\\RcloneUINativePortable\\`; validate actual execution/history and unregister. Confirm no `\\RcloneUI\\` installed task was edited. Test crash, restart, and stale path behavior. Do not use live remotes for the first task test.
9. Move the folder to another writable drive and launch EXE directly again. Verify settings/remote data. Re-select stale absolute paths explicitly; unregister/re-register tasks before switching paths, not by broad registry changes.
10. Copy full Data backup, install new package to new clean folder, restore Data (including empty dirs), run. Roll back with exact matching old Data snapshot. Verify SQLite/JSON schema handling before reusing real credentials.
11. Check notifications and click behavior where offered. Native portable does not register `rclone://` globally; document deep-link limitations. Confirm Windows system caches/Recent Items are identified as OS-owned.
12. Inspect the release SHA256SUMS.txt and compare `Get-FileHash -Algorithm SHA256` output against the published ZIP. Verify binary is unsigned unless separately signed by your own authorized signing process.

**Completion evidence required:** OS build, direct interactive startup, persistence/restart, child process data paths, first/repeated launches, scheduled-task ownership, installed-app coexistence, drive move, upgrade, rollback and trace attribution recorded as separate observations.
