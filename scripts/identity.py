#!/usr/bin/env python3
"""Identity and early duplicate handling: no unrelated tag overwrite."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

PREFIX='native-rcloneui-'
MARKER='<!-- portable-release-publisher:managed:v2 -->'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--release',required=True)
    p.add_argument('--source',required=True)
    p.add_argument('--publisher',required=True)
    p.add_argument('--repo-root',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--github-output',default='')
    a=p.parse_args()
    rec=json.loads(Path(a.release).read_text(encoding='utf-8'))
    pub=json.loads(Path(a.publisher).read_text(encoding='utf-8'))
    root=Path(a.repo_root)
    patch_hash=hashlib.sha256(b''.join((root / p).read_bytes() for p in
                 ('scripts/patch_source.py','scripts/prepare_deps.py',
                  'scripts/validate.py','scripts/package.py'))).hexdigest()
    lock_hash=digest(Path(a.source)/'src-tauri/Cargo.lock')
    npm_hash=digest(Path(a.source)/'package-lock.json')
    # Lockfile changes create distinct releases; source, builder patch revision alone do not
    # hide nonreproducible dependency updates.
    tag=f'{PREFIX}{rec["tag"]}-b1r1-{rec["upstream_commit"][:9]}-{patch_hash[:8]}-{lock_hash[:8]}-{npm_hash[:8]}'
    identity={**rec, 'publisher':pub, 'mode':'NATIVE',
       'builder_revision':'b1r1','builder_commit':os.getenv('GITHUB_SHA','local'),
       'source_patch_sha256':patch_hash,'built_cargo_lock_sha256':lock_hash,
       'built_npm_lock_sha256':npm_hash,'release_tag':tag,
       'platform':'windows-x86_64','installer':None,
       'unverified':['interactive GUI startup','real WebView2 cache containment',
                     'user schedule migration','rclone mount with optional WinFsp',
                     'Windows notifications','drive relocation','real installed-app coexistence']}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    exists=False
    repo=os.environ.get('GITHUB_REPOSITORY','')
    token=os.environ.get('GH_TOKEN','')
    if repo and token:
        url=f'https://api.github.com/repos/{repo}/releases/tags/{tag}'
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,
              'Accept':'application/vnd.github+json','User-Agent':'RcloneUI-Native-Builder'})
        try:
            with urllib.request.urlopen(req,timeout=30) as resp: r=json.load(resp)
            if MARKER not in r.get('body','') or r.get('draft'):
                raise RuntimeError('Existing release tag is not a finished publisher-managed release')
            exists=True
        except urllib.error.HTTPError as e:
            if e.code!=404:raise
        # Check an otherwise unowned git tag, too, not only release lookups.
        if not exists:
            url=f'https://api.github.com/repos/{repo}/git/ref/tags/{tag}'
            req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,
                  'Accept':'application/vnd.github+json','User-Agent':'RcloneUI-Native-Builder'})
            try:
                with urllib.request.urlopen(req,timeout=30):pass
                raise RuntimeError('Tag already exists without valid release; refusing overwrite')
            except urllib.error.HTTPError as e:
                if e.code!=404:raise
    if a.github_output:
        with open(a.github_output,'a',encoding='utf-8',newline='\n') as f:
            f.write(f'release_tag={tag}\n')
            f.write(f'already_exists={str(exists).lower()}\n')
            f.write(f'upstream_version={rec["version"]}\n')
    print(json.dumps({'release_tag':tag,'already_exists':exists},indent=2))

if __name__=='__main__':main()
