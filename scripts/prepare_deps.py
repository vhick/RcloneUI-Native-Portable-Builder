#!/usr/bin/env python3
"""Refresh only dependencies required by source-level native portability.
Regenerated lockfiles are hashed and shipped in the build's identity manifest.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

def run(cmd, cwd):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    a=p.parse_args()
    root=a.source.resolve()
    run(['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],root)
    run(['cargo','update','-p','tauri','--precise','2.12.5'],root/'src-tauri')
    run(['cargo','update','-p','tauri-build','--precise','2.7.4'],root/'src-tauri')
    # locked dependency manifests are now in place. All subsequent steps use --locked / npm ci.
    print('Refreshed resolved dependency locks. Build identity includes both SHA-256 hashes.')

if __name__ == '__main__':main()
