#!/usr/bin/env python3
"""Package the actual source-built GUI executable directly, no launcher/installer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dependencies(src, dest):
    import json
    third={'note':'Inventory only; dependency licenses must be checked before redistribution.',
           'npm':[], 'cargo':[]}
    lock=json.loads((src/'package-lock.json').read_text(encoding='utf-8'))
    for name,value in lock.get('packages',{}).items():
        if name and isinstance(value,dict):
            third['npm'].append({'package':name, 'version':value.get('version'),
                                 'license':value.get('license','SEE SOURCE')})
    # Cargo metadata includes registry dependencies and their license expressions.
    p=subprocess.run(['cargo','metadata','--locked','--format-version','1'],cwd=src/'src-tauri',
                     capture_output=True,text=True,encoding='utf-8',check=True)
    metadata=json.loads(p.stdout)
    for pkg in metadata.get('packages',[]):
        third['cargo'].append({'package':pkg['name'],'version':pkg['version'],
                'license':pkg.get('license') or 'SEE SOURCE','repository':pkg.get('repository')})
    dest.write_text(json.dumps(third,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--identity',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--readme',required=True,type=Path)
    p.add_argument('--github-output',default='')
    a=p.parse_args()
    source=a.source.resolve(); out=a.output_dir.resolve()
    identity=json.loads(a.identity.read_text(encoding='utf-8'))
    stage=out/'RcloneUI-NativePortable'
    if stage.exists():raise RuntimeError(f'Refusing to replace staged data: {stage}')
    stage.mkdir(parents=True)
    (stage/'Data').mkdir()
    (stage/'LICENSES').mkdir()
    binary=source/'src-tauri/target/x86_64-pc-windows-msvc/release/RcloneUI.exe'
    if not binary.is_file():raise RuntimeError(f'No source-built EXE found: {binary}')
    shutil.copy2(binary,stage/'RcloneUI.exe')
    shutil.copy2(source/'LICENSE',stage/'LICENSES/UPSTREAM-LICENSE.txt')
    shutil.copy2(a.readme,stage/'README.txt')
    shutil.copy2(a.identity,stage/'BUILD-IDENTITY.json')
    dependencies(source,stage/'LICENSES/THIRD_PARTY_MANIFEST.json')
    (stage/'README-VERIFY.txt').write_text('See BUILD-IDENTITY.json and release SHA256SUMS.txt.\n'
      'CI validates binary/ZIP but does not prove interactive Windows portability.\n',encoding='utf-8')
    zpath=out/f'RcloneUI-NativePortable-{identity["version"]}-b1r1-win-x64.zip'
    if zpath.exists():raise RuntimeError('Archive exists; refusing overwrite')
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for file in sorted(stage.rglob('*')):
            arc=file.relative_to(stage.parent).as_posix()
            if file.is_dir():z.writestr(arc+'/',b'')
            else:z.write(file,arc)
    digest=sha(zpath)
    (out/(zpath.name+'.sha256')).write_text(f'{digest}  {zpath.name}\n',encoding='utf-8')
    if a.github_output:
        with open(a.github_output,'a',encoding='utf-8',newline='\n') as f:
            f.write(f'zip_path={zpath.relative_to(Path.cwd()).as_posix()}\n')
    print('Created ZIP:',zpath,'SHA256:',digest)

if __name__=='__main__':main()
