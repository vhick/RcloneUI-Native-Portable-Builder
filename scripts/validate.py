#!/usr/bin/env python3
"""Strict NATIVE static validation: PE, manifest, storage code, ZIP layout."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

EXPECTED_EXE='RcloneUI.exe'
EXPECTED_ROOT='RcloneUI-NativePortable'


def pe_machine(path):
    data=Path(path).read_bytes()
    if len(data)<256 or data[:2]!=b'MZ':raise RuntimeError('Missing real MZ header')
    off=struct.unpack_from('<I',data,0x3c)[0]
    if off<64 or off>len(data)-26 or data[off:off+4]!=b'PE\0\0':
        raise RuntimeError('Missing real PE signature')
    machine=struct.unpack_from('<H',data,off+4)[0]
    if machine!=0x8664:raise RuntimeError(f'Expected x64 PE machine 0x8664, got {machine:#x}')
    return machine


def inspect_sources(src):
    lib=(src/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
    main=(src/'src-tauri/src/main.rs').read_text(encoding='utf-8')
    store=(src/'src-tauri/src/scheduler/storeread.rs').read_text(encoding='utf-8')
    zoo=(src/'src-tauri/src/zookeeper.rs').read_text(encoding='utf-8')
    runner=(src/'src-tauri/src/scheduler/runner.rs').read_text(encoding='utf-8')
    sch=(src/'src-tauri/src/scheduler/schtasks.rs').read_text(encoding='utf-8')
    cfg=json.loads((src/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    cargo=(src/'src-tauri/Cargo.toml').read_text(encoding='utf-8')
    checks={
      'runtime Tauri AppDirectoriesOverride':'AppDirectoriesOverride::Root(std::path::PathBuf::from("./Data"))' in lib,
      'Tauri upgraded to >=2.12':'version = "=2.12.5"' in cargo,
      'headless external override cannot bypass Data': 'let (data_dir, local_data_dir) = (None::<String>, None::<String>);' in main,
      'headless current_exe storage root':'std::env::current_exe()' in store and 'root.join("Data")' in store,
      'separate scheduler namespace':'RcloneUINativePortable' in sch,
      'global kill disabled':'refuses to terminate unrelated rclone.exe' in lib,
      'GUI rclone child cache redirected': zoo.count('cmd.env("RCLONE_CACHE_DIR", cache)')==2 and 'native_portable_rclone_paths' in zoo,
      'headless rclone child cache redirected': 'cmd.env("RCLONE_CACHE_DIR", cache)' in runner,
      'PATH integration guarded':'Disabled in native portable: modifying user PATH' in zoo,
      'config sync guarded':'Disabled in native portable: system rclone configuration' in zoo,
      'Windows automatic registration removed':not __import__('re').search(r'(?s)#\[cfg\(windows\)\]\s*\{[^{}]{0,150}app\.deep_link\(\)\.register_all',lib),
      'auto-update plugin absent':'.plugin(tauri_plugin_updater::Builder::new().build())' not in lib,
      'autostart plugin absent':'.plugin(tauri_plugin_autostart::init(' not in lib,
      'Sentry plugin absent':'.plugin(tauri_plugin_sentry::init_with_no_injection(&client))' not in lib,
      'no installer bundle':cfg['bundle']['active'] is False,
      'portable identity':cfg['identifier']=='com.rclone.ui.nativeportable',
      'direct binary name':cfg['mainBinaryName']=='RcloneUI',
    }
    for label,okay in checks.items():print(('PASS' if okay else 'FAIL')+': '+label)
    if not all(checks.values()):raise RuntimeError('Source safety assertion failed')


def check_stage(stage, identity):
    if stage.name!=EXPECTED_ROOT:raise RuntimeError('Native root incorrect')
    if not (stage/EXPECTED_EXE).is_file():raise RuntimeError('Missing executable')
    pe_machine(stage/EXPECTED_EXE)
    if not (stage/'Data').is_dir():raise RuntimeError('Missing persistent Data directory')
    if not (stage/'README.txt').is_file():raise RuntimeError('Missing user README')
    if not (stage/'LICENSES/UPSTREAM-LICENSE.txt').is_file():raise RuntimeError('Missing upstream license')
    if not (stage/'LICENSES/THIRD_PARTY_MANIFEST.json').is_file():raise RuntimeError('Missing dependency attribution manifest')
    if not (stage/'BUILD-IDENTITY.json').is_file():raise RuntimeError('Missing build identity')
    rec=json.loads((stage/'BUILD-IDENTITY.json').read_text(encoding='utf-8'))
    if rec['mode']!='NATIVE' or rec['release_tag']!=identity['release_tag']:
        raise RuntimeError('Wrong identity')
    prohibited=('AppInfo','Other','TraceGuard','ShellGuard','AppNamePortable.exe')
    for entry in stage.rglob('*'):
        if any(s in prohibited for s in entry.relative_to(stage).parts):
            raise RuntimeError(f'Wrong-mode directory discovered: {entry}')
    return {'binary_machine':'x64','binary_sha256':hashlib.sha256((stage/EXPECTED_EXE).read_bytes()).hexdigest()}


def check_zip(zpath, identity):
    if not zipfile.is_zipfile(zpath):raise RuntimeError('Bad ZIP')
    with zipfile.ZipFile(zpath) as z:
        if z.testzip() is not None:raise RuntimeError('ZIP CRC failure')
        paths=z.namelist()
        necessary=(f'{EXPECTED_ROOT}/{EXPECTED_EXE}', f'{EXPECTED_ROOT}/Data/',
                   f'{EXPECTED_ROOT}/BUILD-IDENTITY.json')
        for name in necessary:
            if name not in paths:raise RuntimeError('ZIP missing: '+name)
        if any('..' in Path(name).parts or name.startswith('/') for name in paths):
            raise RuntimeError('Unsafe ZIP path')
        binary=z.read(necessary[0]); off=struct.unpack_from('<I',binary,0x3c)[0]
        if binary[off:off+4]!=b'PE\0\0':raise RuntimeError('Archive binary corrupted')
        ident=json.loads(z.read(necessary[2]))
        if ident['release_tag']!=identity['release_tag']:raise RuntimeError('ZIP identity mismatch')
    return hashlib.sha256(zpath.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--stage',type=Path)
    p.add_argument('--zip',type=Path)
    p.add_argument('--identity',type=Path)
    a=p.parse_args()
    inspect_sources(a.source)
    ident=json.loads(a.identity.read_text(encoding='utf-8')) if a.identity else {}
    if a.stage:
        info=check_stage(a.stage,ident)
        print('WINDOWS-COMPILED static PE verified:', json.dumps(info))
    if a.zip:
        checksum=check_zip(a.zip,ident)
        print('STATIC-VALIDATED native ZIP SHA-256:',checksum)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('VALIDATION FAILED:',exc,file=sys.stderr)
        sys.exit(1)
