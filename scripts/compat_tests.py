#!/usr/bin/env python3
"""Source-evidenced compatibility fixes for upstream *tests* only.

Never skips or marks a failed test successful. This module does not modify
production Rust behavior. Narrow adapters are applied only when the upstream
source still exhibits the exact, reviewed cross-platform fixture mistake.
"""
import re

UPSTREAM_TEST = 'unzip_extracts_files_and_modes'
WINDOWS_WRONG_FIXTURE = '                ("rclone-v1-osx/rclone", b"binary contents", 0o755),'
PORTABLE_FIXTURE = '                (zip_binary_name.as_str(), b"binary contents", 0o755),'
DYNAMIC_NAME = '        let zip_binary_name = format!("rclone-v1-osx/{}", bin_name());\n'
TEST_RE = re.compile(
    r'(?P<prefix>    #\[test\]\n    fn unzip_extracts_files_and_modes\(\) \{)'
    r'(?P<body>.*?)'
    r'(?=\n    #\[test\]|\n\})', re.S)


def adapt_upstream_cross_platform_tests(source: str) -> tuple[str, str]:
    """Correct one known test-only Unix executable fixture on Windows.

    Returns (source, status). A future test already updated by upstream, or a
    removed/renamed test, is left intact. A still-broken fixture with changed
    anchors fails closed rather than silently skipping or weakening tests.
    """
    matches = list(TEST_RE.finditer(source))
    if not matches:
        if f'fn {UPSTREAM_TEST}(' in source:
            raise RuntimeError('Upstream zip test structure changed; inspect before modifying it')
        return source, 'upstream zip fixture test not present; nothing to modify'
    if len(matches) != 1:
        raise RuntimeError('Ambiguous upstream zip tests; refusing automatic test patch')
    m = matches[0]
    body = m.group('body')
    if WINDOWS_WRONG_FIXTURE not in body:
        if '"rclone-v1-osx/rclone"' in body:
            raise RuntimeError('Upstream Unix-only binary fixture changed shape; requires source review')
        return source, 'upstream zip fixture already differs from known broken pattern; unchanged'

    # Make sure the behavior that causes this test failure is still present.
    # The app correctly searches for rclone.exe on Windows, so changing
    # find_binary to accept an extensionless executable would be unsafe.
    if 'fn bin_name()' not in source or '"rclone.exe"' not in source:
        raise RuntimeError('Cannot verify Windows rclone executable name')
    if not re.search(r'fn find_binary\(dir: &Path\) -> Option<PathBuf> \{\s*let target = bin_name\(\);', source):
        raise RuntimeError('Upstream binary lookup semantics changed; needs audit')

    target = '        write_zip(\n'
    if body.count(target) != 1 or body.count(WINDOWS_WRONG_FIXTURE) != 1:
        raise RuntimeError('ZIP fixture construction changed; refusing broad patch')
    body = body.replace(target, DYNAMIC_NAME + target, 1)
    body = body.replace(WINDOWS_WRONG_FIXTURE, PORTABLE_FIXTURE, 1)
    corrected = source[:m.start('body')] + body + source[m.end('body'):]
    assert corrected.count(PORTABLE_FIXTURE) == 1
    return corrected, 'adapted test ZIP fixture to platform-specific bin_name()'
