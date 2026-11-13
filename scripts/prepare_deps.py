#!/usr/bin/env python3
"""Refresh only dependencies required by source-level native portability.
Regenerated lockfiles are hashed and shipped in the build's identity manifest.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
from verify_tauri import check_versions

def resolved_command(cmd, platform=None):
    """Resolve Node's Windows .cmd shims explicitly without a shell.

    Windows CreateProcess cannot reliably discover npm/npx batch shims by
    extensionless name. The runner must execute npm.cmd, not npm.
    No shell=True: arguments stay as an explicit list.
    """
    platform = sys.platform if platform is None else platform
    result = list(cmd)
    if platform == 'win32' and result and result[0].lower() in ('npm', 'npx'):
        result[0] += '.cmd'
    return result


def run(cmd, cwd):
    command = resolved_command(cmd)
    # Give an actionable error instead of a cryptic WinError 2.
    if shutil.which(command[0]) is None:
        raise RuntimeError(f"Required build command not on PATH: {command[0]}")
    print('+', ' '.join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    a=p.parse_args()
    root=a.source.resolve()
    run(['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],root)
    run(['cargo','update','-p','tauri','--precise','2.12.5'],root/'src-tauri')
    run(['cargo','update','-p','tauri-build','--precise','2.7.4'],root/'src-tauri')
    check_versions(root)  # test resolved versions BEFORE npm ci or expensive Rust build
    # locked dependency manifests are now in place. All subsequent steps use --locked / npm ci.
    print('Refreshed resolved dependency locks. Build identity includes both SHA-256 hashes.')

if __name__ == '__main__':main()
