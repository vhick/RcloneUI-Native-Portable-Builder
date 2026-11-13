RCLONE UI - NATIVE PORTABLE (UNOFFICIAL WINDOWS X64 BUILD)
==========================================================

1. Extract the complete RcloneUI-NativePortable directory anywhere writable,
   including folders containing spaces or Unicode characters. Avoid Program Files
   or protected folders. Run RcloneUI.exe directly. NO LAUNCHER IS REQUIRED.
2. Data is created/persisted next to RcloneUI.exe in Data\. Keep this folder.
   Tauri app/config/local/webview/cache/log paths are redirected before the
   window/webview starts via Tauri 2.12 AppDirectoriesOverride. Standalone
   headless scheduled task processes resolve Data from their own EXE path.
3. Rclone UI normally offers download/management of rclone binaries from inside
   the application. The rclone binary can be downloaded into Data by the GUI.
   Child processes use Data\rclone-cache for normal rclone caching and the
   Data\rclone.conf default unless you explicitly choose another config.
   This package does not claim an offline-bundled rclone.exe. Rclone mounts on
   Windows may need installed WinFsp (outside this portable package).
4. Native portable does NOT automatically install user-login startup, PATH,
   rclone:// links, Windows associations, services, or shortcuts. No elevation
   should be necessary for ordinary GUI use. Global rclone process termination,
   PATH integration, system-config sync, updater, autostart plugin, automatic
   protocol registration and Sentry native crash telemetry have been disabled
   in this variant to protect existing host applications. Some upstream UI
   controls for those features will return a clear error or be unavailable.
5. Scheduling is a SEPARATE intentional host integration: if you create an OS
   schedule through the GUI, it registers Windows Task Scheduler tasks under
   \RcloneUINativePortable\. This is NOT automatic on a fresh run. It persists
   after closing the GUI. Disable/remove tasks from the GUI BEFORE moving,
   upgrading incompatibly or deleting the portable folder. Test the task in a
   real Windows desktop; Task Scheduler execution is not proved by headless CI.
6. After moving portable folders/drives, any saved custom absolute file paths,
   externally specified directories, rclone paths, task XML and cloud-mount
   destinations may become stale. Re-select those paths explicitly. Do not
   expect arbitrary absolute paths in rclone.conf to be rewritten silently.
7. SAFE UPGRADES: quit GUI and stop managed background jobs, remove registered
   scheduled tasks if the drive path will change, make a full Data backup,
   extract newer package to a DIFFERENT empty folder, and copy your existing
   Data\ directory to the new folder with all nested/empty directories intact.
   Never replace/delete Data. Do not run old and new binaries against the same
   Data concurrently. Run a data-schema compatibility check manually before
   first launch if changing major versions.
8. ROLLBACK: close app and all scheduled tasks. Preserve a pre-upgrade Data
   backup. Restore matching old EXE and matching Data snapshot. A newer app may
   migrate stored data in ways the older app cannot read. Do not mix schemas.
9. Credentials in rclone.conf and Tauri stores may be sensitive. Portable Data
   is not automatically encrypted and a USB stick can be lost. Some provider
   credentials may be tied to your Windows account/device. Protect your drive.
10. Windows-managed activity (recent files, DNS, OS event logs, thumbnail and
    shell caches, firewall prompts, WebView2 runtime installation, Windows
    notifications) may remain on the host. Do NOT assume no Windows traces.
11. Microsoft Edge WebView2 Runtime is a system prerequisite; it is not bundled
    in this ZIP. An optional WinFsp installation is required for mount features.
12. Build verification status is described in BUILD-IDENTITY.json. A successful
    hosted Windows compile and headless test DO NOT prove GUI portability.

This package is not an official rclone/rclone-ui release. Preserve upstream
Apache-2.0 license and review the third-party dependency license inventory.
