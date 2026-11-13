#!/usr/bin/env python3
"""Source retrieval: exact published tag only, checkout detached and record full SHA."""
import argparse
import json
import os
from pathlib import Path
import subprocess

URL = 'https://github.com/rclone/rclone-ui.git'

def run(*args, cwd=None):
    print('+', *args, flush=True)
    subprocess.run(args, cwd=cwd, check=True)

def output(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, encoding='utf-8').strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--release', required=True)
    p.add_argument('--source', required=True)
    a = p.parse_args()
    record = json.loads(Path(a.release).read_text(encoding='utf-8'))
    tag = record['tag']
    src = Path(a.source).resolve()
    if src.exists():
        raise RuntimeError(f'Source directory already exists; refusing reuse: {src}')
    src.mkdir(parents=True)
    run('git', 'init', '-q', str(src))
    run('git', 'remote', 'add', 'origin', URL, cwd=src)
    run('git', '-c', 'protocol.version=2', 'fetch', '--depth=1', '--no-tags', 'origin', f'refs/tags/{tag}', cwd=src)
    run('git', '-c', 'advice.detachedHead=false', 'checkout', '--detach', 'FETCH_HEAD', cwd=src)
    sha = output('git', 'rev-parse', 'HEAD', cwd=src)
    if not len(sha)==40 or any(c not in '0123456789abcdef' for c in sha):
        raise RuntimeError('Invalid upstream full SHA')
    for rel in ('src-tauri/src/lib.rs','src-tauri/src/main.rs','src-tauri/src/zookeeper.rs',
                'src-tauri/src/scheduler/storeread.rs','src-tauri/Cargo.lock',
                'package-lock.json','LICENSE'):
        if not (src / rel).is_file():
            raise RuntimeError(f'Missing required upstream source file: {rel}')
    cfg = json.loads((src/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    pkg = json.loads((src/'package.json').read_text(encoding='utf-8'))
    if cfg['version'] != record['version'] or pkg['version'] != record['version']:
        raise RuntimeError('Upstream tag, Tauri version and npm version mismatch')
    record['upstream_commit'] = sha
    record['original_cargo_lock_sha256'] = __import__('hashlib').sha256((src/'src-tauri/Cargo.lock').read_bytes()).hexdigest()
    record['original_npm_lock_sha256'] = __import__('hashlib').sha256((src/'package-lock.json').read_bytes()).hexdigest()
    Path(a.release).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(f'Checked out {tag} @ {sha}')

if __name__ == '__main__':
    main()
