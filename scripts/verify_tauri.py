#!/usr/bin/env python3
"""Fail early if the resolved npm Tauri core API mismatches the Rust core.

This checks actual lockfile versions, not optimistic package.json ranges.
"""
import argparse
import json
from pathlib import Path
import tomllib

EXPECTED_RUST = '2.12.5'
EXPECTED_API = '2.12.3'
EXPECTED_CLI = '2.12.4'


def major_minor(value):
    values = value.split('.')
    if len(values) < 2 or not values[0].isdigit() or not values[1].isdigit():
        raise RuntimeError(f'Unrecognized dependency version: {value}')
    return tuple(map(int, values[:2]))


def check_versions(source, installed=False):
    source = Path(source)
    npm_lock = json.loads((source / 'package-lock.json').read_text(encoding='utf-8'))
    packages = npm_lock['packages']
    npm_api = packages['node_modules/@tauri-apps/api']['version']
    npm_cli = packages['node_modules/@tauri-apps/cli']['version']
    crates = tomllib.loads((source / 'src-tauri/Cargo.lock').read_text(encoding='utf-8'))['package']
    rust_tauri = [p['version'] for p in crates if p['name'] == 'tauri']
    if len(rust_tauri) != 1:
        raise RuntimeError(f'Expected exactly one resolved Rust tauri crate, found {rust_tauri!r}')
    rust_tauri = rust_tauri[0]
    if rust_tauri != EXPECTED_RUST or npm_api != EXPECTED_API or npm_cli != EXPECTED_CLI:
        raise RuntimeError(f'Tauri version lock mismatch: Rust tauri={rust_tauri}, '
                           f'JS @tauri-apps/api={npm_api}, CLI={npm_cli}; '
                           f'expected {EXPECTED_RUST} / {EXPECTED_API} / {EXPECTED_CLI}')
    if major_minor(rust_tauri) != major_minor(npm_api):
        raise RuntimeError(f'Tauri Rust/JS major.minor mismatch: {rust_tauri} vs {npm_api}')
    pkg = json.loads((source / 'package.json').read_text(encoding='utf-8'))
    declared = [pkg[section]['@tauri-apps/api'] for section in ('dependencies', 'devDependencies')
                if '@tauri-apps/api' in pkg.get(section, {})]
    if not declared or any(version != EXPECTED_API for version in declared):
        raise RuntimeError(f'Tauri JS manifest is not pinned to {EXPECTED_API}: {declared}')
    if installed:
        actual = json.loads((source / 'node_modules/@tauri-apps/api/package.json').read_text(encoding='utf-8'))['version']
        if actual != npm_api:
            raise RuntimeError(f'Installed Tauri JS API version {actual} != lockfile version {npm_api}')
    print(f'PASS: Rust tauri {rust_tauri}; JS API {npm_api}; CLI {npm_cli}' +
          ('; installed API matches' if installed else '; lockfiles match'))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--source', required=True, type=Path)
    a.add_argument('--installed', action='store_true')
    opts = a.parse_args()
    check_versions(opts.source, opts.installed)


if __name__ == '__main__':
    main()
