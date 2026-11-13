#!/usr/bin/env python3
"""Check the selected publisher tag and live action.yml interface BEFORE publish."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

API='https://api.github.com/repos/vhick/portable-release-publisher'
RAW='https://raw.githubusercontent.com/vhick/portable-release-publisher/v1.1.1/action.yml'
EXPECTED=('files','tag','release-title','tag-prefix','keep-releases','prune','dry-run')

def request(url):
    headers={'Accept':'application/vnd.github+json','User-Agent':'RcloneUI-Native-Builder-b1r2'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=40) as response:
        return response.read()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True)
    a=p.parse_args()
    ref=json.loads(request(API+'/git/ref/tags/v1.1.1'))
    obj=ref['object']
    if obj['type']=='tag':
        obj=json.loads(request(API+'/git/tags/'+obj['sha']))['object']
    if obj['type']!='commit' or len(obj['sha'])!=40:
        raise RuntimeError('Publisher v1.1.1 did not resolve to a commit')
    raw=request(RAW)
    data=raw.decode('utf-8')
    for key in EXPECTED:
        if not re.search(r'(?m)^  '+re.escape(key)+r':\s*$',data):
            raise RuntimeError(f'Publisher action.yml missing input {key}')
    if ('using: composite' not in data or
            'python "$GITHUB_ACTION_PATH/scripts/publish.py"' not in data or
            "GH_TOKEN: ${{ github.token }}" not in data):
        raise RuntimeError('Unexpected publisher implementation / permissions')
    summary={'action':'vhick/portable-release-publisher@v1.1.1',
             'resolved_commit':obj['sha'], 'action_yml_sha256':hashlib.sha256(raw).hexdigest(),
             'expected_inputs':list(EXPECTED),'publication_target':'calling repository'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
