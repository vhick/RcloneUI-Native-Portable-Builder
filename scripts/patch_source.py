#!/usr/bin/env python3
"""Fail-closed, application-specific adapters for rclone-ui v3.7.5+ source.

No wrappers. All modifications run against a verified upstream Git checkout.
Any upstream refactor that breaks an anchor BLOCKS release rather than silently
building without a critical data-safety patch.
"""
import argparse
import json
import re
from pathlib import Path

TAURI_API_VERSION = '2.12.3'  # stable upstream API: same 2.12 minor as Rust 2.12.5


def pin_tauri_api(pkg):
    """Pin the actual JS dependency, whether upstream uses deps or devDeps."""
    matches = []
    for section in ('dependencies', 'devDependencies'):
        block = pkg.get(section, {})
        if '@tauri-apps/api' in block:
            matches.append(section)
    if not matches:
        raise RuntimeError('Missing upstream @tauri-apps/api dependency; audit source before updating')
    for section in matches:
        pkg[section]['@tauri-apps/api'] = TAURI_API_VERSION
    return pkg

APP_IDENTIFIER = 'com.rclone.ui.nativeportable'
MAIN_BINARY = 'RcloneUI'


def replace_once(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one exact source anchor; found {count}')
    return s.replace(old, new, 1)


def replace_regex(s, pattern, new, label):
    s, n = re.subn(pattern, new, s, count=0, flags=re.MULTILINE | re.DOTALL)
    if n != 1:
        raise RuntimeError(f'{label}: expected one matching block; found {n}')
    return s


def apply(root):
    cfg_file = root/'src-tauri/tauri.conf.json'
    cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
    assert cfg['identifier'] == 'com.rclone.ui', 'Unexpected upstream Tauri identifier'
    assert cfg['mainBinaryName'] == 'Rclone UI', 'Unexpected upstream binary name'
    assert cfg['app']['windows'][0].get('dataDirectory') is None, 'Window has an independent data directory'
    cfg['identifier'] = APP_IDENTIFIER
    cfg['mainBinaryName'] = MAIN_BINARY
    # No PortableApps bundle or installer in NATIVE mode. CI builds --no-bundle.
    cfg['bundle']['active'] = False
    cfg['bundle']['createUpdaterArtifacts'] = False
    cfg['bundle']['windows'].pop('signCommand', None)
    # Installed application's `rclone://` handler is never registered by the portable build.
    cfg.get('plugins', {}).pop('updater', None)
    cfg.get('plugins', {}).pop('deep-link', None)
    cfg_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

    cargo_path = root/'src-tauri/Cargo.toml'
    cargo = cargo_path.read_text(encoding='utf-8')
    cargo = replace_regex(cargo,
        r'(?m)^tauri = \{ version = "[^"]+", features =',
        'tauri = { version = "=2.12.5", features =', 'pin tauri 2.12.5')
    cargo = replace_regex(cargo,
        r'(?m)^tauri-build = \{ version = "[^"]+", features =',
        'tauri-build = { version = "=2.7.4", features =', 'pin tauri-build')
    cargo = replace_once(cargo, 'name = "app"', 'name = "app"\nautobins = false', 'disable ambiguous Cargo app.exe')
    cargo += '\n[[bin]]\nname = "RcloneUI"\npath = "src/main.rs"\n'
    cargo_path.write_text(cargo, encoding='utf-8')

    package_path = root/'package.json'
    pkg = json.loads(package_path.read_text(encoding='utf-8'))
    deps = pkg.get('devDependencies', {})
    if '@tauri-apps/cli' not in deps:
        raise RuntimeError('Missing upstream @tauri-apps/cli dev dependency')
    deps['@tauri-apps/cli'] = '2.12.4'
    # The Tauri CLI refuses to build if its Rust core and JS core use
    # different major/minor versions. Upstream's api 2.11.0 must be updated
    # alongside tauri 2.12.5. Fail closed if the expected API is absent.
    pin_tauri_api(pkg)
    package_path.write_text(json.dumps(pkg, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

    lib_path = root/'src-tauri/src/lib.rs'
    lib = lib_path.read_text(encoding='utf-8')
    # No app/plugin-owned writes before runtime path override. Keep it rooted in
    # *the executable*, not the current working directory (Tauri 2.12 API).
    lib = replace_once(lib,
        '    let client = sentry::init((',
        '    /* NATIVE PORTABLE: crash telemetry/minidump initialization disabled.\n'
        '    let client = sentry::init((', 'Sentry start')
    lib = replace_once(lib,
        '    let _guard = tauri_plugin_sentry::minidump::init(&client);',
        '    let _guard = tauri_plugin_sentry::minidump::init(&client);\n'
        '    */\n', 'Sentry end')
    lib = replace_once(lib, '        .plugin(tauri_plugin_sentry::init_with_no_injection(&client))\n',
                       '', 'Sentry plugin')
    lib = replace_once(lib, '        .plugin(tauri_plugin_updater::Builder::new().build())\n',
                       '', 'unsafe self-update plugin')
    # Native portable must never automatically register an unowned HKCU Run entry.
    lib = replace_regex(lib,
        r'\s*\.plugin\(tauri_plugin_autostart::init\(\s*tauri_plugin_autostart::MacosLauncher::LaunchAgent,\s*Some\(vec!\[\]\),\s*\)\)',
        '\n', 'autostart plugin')
    lib = replace_regex(lib,
        r'(?m)^\s*#\[cfg\(windows\)\]\s*\{\s*use tauri_plugin_deep_link::DeepLinkExt;\s*if let Err\(err\) = app\.deep_link\(\)\.register_all\(\) \{\s*log::warn!\("deep-link registration failed \(continuing\): \{\}", err\);\s*\}\s*\}',
        '\n            // Native portable: never replace system rclone:// protocol owner.',
        'automatic Windows protocol registration')
    lib = replace_regex(lib,
        r'(?m)^#\[tauri::command\]\s*async fn stop_rclone_processes\([^)]*\) -> Result<u32, String> \{.*?\n\}\n\n(?=async fn prompt_text)',
        '#[tauri::command]\n'
        'async fn stop_rclone_processes(_timeout_ms: Option<u64>) -> Result<u32, String> {\n'
        '    Err("Native portable refuses to terminate unrelated rclone.exe processes. Use the managed-daemon stop control instead.".into())\n'
        '}\n\n',
        'dangerous global rclone process killer')
    lib = replace_once(lib,
        '        .build(tauri::generate_context!())',
        '        .build({\n'
        '            let mut context = tauri::generate_context!();\n'
        '            #[cfg(target_os = "windows")]\n'
        '            {\n'
        '                use tauri::utils::config::AppDirectoriesOverride;\n'
        '                // Tauri 2.12 resolves relative paths against the RUNNING EXE directory.\n'
        '                context.config_mut().app.app_directories_override =\n'
        '                    Some(AppDirectoriesOverride::Root(std::path::PathBuf::from("./Data")));\n'
        '            }\n'
        '            context\n'
        '        })', 'Tauri in-process portable path override')
    lib_path.write_text(lib, encoding='utf-8')

    # A manually supplied --data-dir flag or a stale scheduler argument must
    # never bypass the portable root on Windows. The data root is always
    # derived by storeread::app_dirs() from the current EXE.
    main_path = root/'src-tauri/src/main.rs'
    main = main_path.read_text(encoding='utf-8')
    main = replace_once(main,
        '        let local_data_dir = flag_value("--local-data-dir");',
        '        let local_data_dir = flag_value("--local-data-dir");\n'
        '        #[cfg(target_os = "windows")]\n'
        '        let (data_dir, local_data_dir) = (None::<String>, None::<String>);',
        'prevent headless Windows --data-dir bypass')
    main_path.write_text(main, encoding='utf-8')

    # Headless scheduled runs initialize no Tauri app; patch their independent
    # path resolution, even when invoked from Task Scheduler on an arbitrary cwd.
    store_path = root/'src-tauri/src/scheduler/storeread.rs'
    store = store_path.read_text(encoding='utf-8')
    store = replace_once(store,
        'const APP_IDENTIFIER: &str = "com.rclone.ui";',
        f'const APP_IDENTIFIER: &str = "{APP_IDENTIFIER}";', 'headless app identity')
    store = replace_regex(store,
        r'pub fn app_dirs\(\) -> Result<AppDirs, String> \{.*?\n\}',
        'pub fn app_dirs() -> Result<AppDirs, String> {\n'
        '    #[cfg(target_os = "windows")]\n'
        '    {\n'
        '        let exe = std::env::current_exe()\n'
        '            .map_err(|e| format!("cannot locate running executable: {e}"))?;\n'
        '        let root = exe.parent().ok_or("executable has no parent directory")?;\n'
        '        let data = root.join("Data");\n'
        '        return Ok(AppDirs { app_data: data.clone(), app_local_data: data });\n'
        '    }\n'
        '    #[cfg(not(target_os = "windows"))]\n'
        '    {\n'
        '        let data = dirs::data_dir().ok_or("could not resolve user data")?;\n'
        '        let local = dirs::data_local_dir().ok_or("could not resolve local data")?;\n'
        '        Ok(AppDirs { app_data: data.join(APP_IDENTIFIER),\n'
        '            app_local_data: local.join(APP_IDENTIFIER) })\n'
        '    }\n'
        '}', 'headless store location')
    store_path.write_text(store, encoding='utf-8')

    scheduler_path = root/'src-tauri/src/scheduler/schtasks.rs'
    sch = scheduler_path.read_text(encoding='utf-8')
    sch = replace_once(sch, 'const TASK_FOLDER: &str = "RcloneUI";',
                       'const TASK_FOLDER: &str = "RcloneUINativePortable";',
                       'Windows scheduled-task namespace isolation')
    scheduler_path.write_text(sch, encoding='utf-8')

    zoo_path = root/'src-tauri/src/zookeeper.rs'
    zoo = zoo_path.read_text(encoding='utf-8')
    zoo = replace_once(zoo,
        'use tauri::{AppHandle, Emitter, Manager};',
        'use tauri::{AppHandle, Emitter, Manager};\n'
        '\n'
        '#[cfg(target_os = "windows")]\n'
        'fn native_portable_rclone_paths() -> Result<(PathBuf, PathBuf), String> {\n'
        '    let exe = std::env::current_exe().map_err(|e| e.to_string())?;\n'
        '    let root = exe.parent().ok_or("no executable parent directory")?;\n'
        '    let data = root.join("Data");\n'
        '    let cache = data.join("rclone-cache");\n'
        '    std::fs::create_dir_all(&cache).map_err(|e| e.to_string())?;\n'
        '    Ok((cache, data.join("rclone.conf")))\n'
        '}\n', 'native rclone child cache resolver')
    # All rclone children receive an isolated cache. GUI-defined RCLONE_CONFIG
    # may be deliberately supplied for a selected app-owned or external config;
    # only absent config gets the adjacent default, so installed rclone profiles
    # are never accidentally selected by the CLI's default search order.
    zoo = replace_once(zoo,
        '    cmd.stdin(if stdin_lines.is_some() {',
        '    #[cfg(target_os = "windows")]\n'
        '    {\n'
        '        let (cache, config) = native_portable_rclone_paths()?;\n'
        '        cmd.env("RCLONE_CACHE_DIR", cache);\n'
        '        if !env.contains_key("RCLONE_CONFIG") { cmd.env("RCLONE_CONFIG", config); }\n'
        '    }\n'
        '    cmd.stdin(if stdin_lines.is_some() {',
        'isolate one-shot rclone cache and default config')
    zoo = replace_once(zoo,
        '    // Nothing consumes daemon stdio; null it to avoid pipe-fill and extra threads.',
        '    #[cfg(target_os = "windows")]\n'
        '    {\n'
        '        let (cache, config) = native_portable_rclone_paths()?;\n'
        '        cmd.env("RCLONE_CACHE_DIR", cache);\n'
        '        if !env.contains_key("RCLONE_CONFIG") { cmd.env("RCLONE_CONFIG", config); }\n'
        '    }\n'
        '    // Nothing consumes daemon stdio; null it to avoid pipe-fill and extra threads.',
        'isolate managed rclone daemon cache/default config')
    # Prevent touching HKCU user PATH or installed rclone configuration. The GUI
    # remains functional for managed rclone, but these opt-in system integrations
    # are explicitly unsupported by the portable flavor.
    guard_path = '''\n    #[cfg(target_os = "windows")]\n    {\n        let _ = (&app, enable, &target_path);\n        return Err("Disabled in native portable: modifying user PATH would leave stale host entries after relocation".into());\n    }\n'''
    zoo = replace_regex(zoo,
        r'(pub fn set_rclone_path_integration\(\s*app: AppHandle,\s*enable: bool,\s*target_path: String,\s*\) -> Result<PathStatus, String> \{)',
        r'\g<1>' + guard_path.replace('\\','\\\\'),
        'Windows PATH writing guard')
    sync_guard = '''\n    #[cfg(target_os = "windows")]\n    {\n        let _ = (&app, enable, &app_config_path, &owned_link_target, &default_config_path);\n        return Err("Disabled in native portable: system rclone configuration must stay untouched".into());\n    }\n'''
    zoo = replace_regex(zoo,
        r'(pub fn set_config_sync\(\s*app: AppHandle,\s*enable: bool,\s*app_config_path: String,\s*owned_link_target: Option<String>,\s*default_config_path: Option<String>,\s*\) -> Result<ConfigSyncStatus, String> \{)',
        r'\g<1>' + sync_guard.replace('\\','\\\\'),
        'system rclone config sync guard')
    zoo_path.write_text(zoo, encoding='utf-8')

    runner_path = root/'src-tauri/src/scheduler/runner.rs'
    runner = runner_path.read_text(encoding='utf-8')
    runner = replace_once(runner,
        '    cmd.stdin(Stdio::null());',
        '    #[cfg(target_os = "windows")]\n'
        '    {\n'
        '        let cache = dirs.app_local_data.join("rclone-cache");\n'
        '        if let Err(e) = std::fs::create_dir_all(&cache) {\n'
        '            return RunOutcome::setup(format!("cannot create portable rclone cache: {e}"));\n'
        '        }\n'
        '        cmd.env("RCLONE_CACHE_DIR", cache);\n'
        '    }\n'
        '    cmd.stdin(Stdio::null());',
        'isolate scheduled rclone cache')
    runner_path.write_text(runner, encoding='utf-8')
    print('Applied NATIVE source-level portability and host protection adapters.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream', type=Path)
    args = ap.parse_args()
    apply(args.upstream.resolve())
