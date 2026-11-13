#!/usr/bin/env python3
"""Resolve a published stable rclone/rclone-ui release by numeric version.

GitHub Releases pagination is deliberate: /releases/latest is not suitable for
projects with prerelease/side-product release streams.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = 'https://api.github.com/repos/rclone/rclone-ui'
STABLE = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')


def get_json(url, token=''):
    h = {'User-Agent': 'RcloneUI-Native-Builder-b1r1', 'Accept': 'application/vnd.github+json',
         'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        h['Authorization'] = f'Bearer {token}'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=45) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f'GitHub resource not found (404): {url}') from e
        raise RuntimeError(f'GitHub API failure {e.code}: {url}') from e


def choose_release(items, wanted):
    eligible = {}
    for r in items:
        if r.get('draft') or r.get('prerelease'):
            continue
        tag = r.get('tag_name', '')
        match = STABLE.fullmatch(tag)
        if match:
            eligible[tag] = (tuple(map(int, match.groups())), r)
    if wanted == 'latest':
        if not eligible:
            raise ValueError('No suitable published stable vX.Y.Z release found')
        return max(eligible.values(), key=lambda x: x[0])[1]
    wanted = wanted if wanted.startswith('v') else 'v' + wanted
    if not STABLE.fullmatch(wanted):
        raise ValueError(f'Only stable vX.Y.Z releases accepted: {wanted!r}')
    if wanted not in eligible:
        raise ValueError(f'Explicit stable release {wanted} not found in published releases')
    return eligible[wanted][1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--version', default='latest')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    token = os.getenv('GH_TOKEN', '')
    releases = []
    for page in range(1, 11):
        batch = get_json(f'{API}/releases?per_page=100&page={page}', token)
        if not isinstance(batch, list):
            raise RuntimeError('Unexpected GitHub releases API response')
        releases.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError('Pagination exceeded 1,000 releases; refusing ambiguous latest')
    release = choose_release(releases, a.version)
    result = {'upstream_repository': 'rclone/rclone-ui', 'tag': release['tag_name'],
              'version': release['tag_name'][1:], 'release_url': release['html_url'],
              'release_id': release['id'], 'target_commitish': release.get('target_commitish')}
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
