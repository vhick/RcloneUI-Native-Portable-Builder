#!/usr/bin/env python3
"""Hosted-Windows-safe process entrypoint smoke check; not a GUI portability test."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--exe',type=Path,required=True)
    a=p.parse_args()
    if sys.platform!='win32':raise RuntimeError('This test must execute on Windows')
    # Deliberately invalid task ID must be rejected before any app or browser initialization.
    result=subprocess.run([str(a.exe.resolve()),'run-task','INVALID@TASK'],
          cwd=Path.home(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
          encoding='utf-8',errors='replace',timeout=20)
    if result.returncode!=2 or 'invalid task id' not in result.stderr:
        raise RuntimeError(f'Unexpected headless behavior: exit={result.returncode}\n{result.stderr}')
    print('AUTOMATED-RUNTIME-TESTED: source-built EXE accepted direct command invocation and rejected invalid task ID.')
    print('NOT VERIFIED: interactive GUI/tray/WebView2/cache/notifications, remotes, scheduled task execution.')

if __name__=='__main__':main()
