import json
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from resolve import choose_release
from validate import pe_machine, check_zip
from patch_source import replace_once, replace_regex, pin_tauri_api, TAURI_API_VERSION
from prepare_deps import resolved_command, run
from verify_tauri import check_versions, major_minor
from unittest import mock


class StableResolverTests(unittest.TestCase):
    def test_numeric_version_sort(self):
        records=[{'tag_name':x,'draft':False,'prerelease':False} for x in
                 ('v3.9.9','v3.10.0','v4.0.0-beta.3','cloud-v7.0.0','v3.7.5')]
        self.assertEqual(choose_release(records,'latest')['tag_name'],'v3.10.0')
    def test_no_prerelease(self):
        self.assertEqual(choose_release([{'tag_name':'v3.7.5','draft':False,'prerelease':False},
                 {'tag_name':'v4.0.0','draft':False,'prerelease':True}], 'latest')['tag_name'],'v3.7.5')
    def test_explicit_nonstable_rejected(self):
        with self.assertRaises(ValueError):choose_release([], 'v4.0.0-beta.3')

class SourceSafetyTests(unittest.TestCase):
    def test_fail_closed_anchor(self):
        with self.assertRaises(RuntimeError):replace_once('foo','missing','other','test')
    def test_exact_regex(self):
        self.assertEqual(replace_regex('foo','foo','bar','t'),'bar')
        with self.assertRaises(RuntimeError):replace_regex('foofoo','foo','bar','t')

class WindowsNpmLaunchTests(unittest.TestCase):
    def test_windows_npm_uses_cmd_shim(self):
        self.assertEqual(resolved_command(['npm','install','--no-audit'], 'win32'),
                         ['npm.cmd','install','--no-audit'])
        self.assertEqual(resolved_command(['npx','--version'], 'win32'),
                         ['npx.cmd','--version'])

    def test_linux_command_remains_unchanged(self):
        self.assertEqual(resolved_command(['npm','ci'], 'linux'), ['npm','ci'])
        self.assertEqual(resolved_command(['cargo','update'], 'win32'), ['cargo','update'])

    def test_win32_launcher_passes_cmd_to_subprocess_without_shell(self):
        # Cross-platform simulation; real GitHub Windows build remains required.
        with mock.patch('prepare_deps.sys.platform','win32'), \
             mock.patch('prepare_deps.shutil.which',return_value=r'C:\nodejs\npm.cmd') as which, \
             mock.patch('prepare_deps.subprocess.run') as spawn:
            run(['npm','install'],Path('some source path'))
            which.assert_called_once_with('npm.cmd')
            spawn.assert_called_once_with(['npm.cmd','install'],
                                          cwd=Path('some source path'),check=True)

    def test_missing_executable_fails_before_spawn(self):
        with mock.patch('prepare_deps.sys.platform','win32'), \
             mock.patch('prepare_deps.shutil.which',return_value=None), \
             mock.patch('prepare_deps.subprocess.run') as spawn:
            with self.assertRaisesRegex(RuntimeError,'npm.cmd'):
                run(['npm','install'],Path('.'))
            spawn.assert_not_called()

class BinaryTests(unittest.TestCase):
    def test_reject_dummy_mz(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'fake.exe'; f.write_bytes(b'MZ'+b'\0'*254)
            with self.assertRaises(RuntimeError):pe_machine(f)


class TauriDependencyCoherenceTests(unittest.TestCase):
    def test_upstream_core_api_is_upgraded_in_dependencies(self):
        original = {'dependencies': {'@tauri-apps/api': '2.11.0'},
                    'devDependencies': {'@tauri-apps/cli': '2.12.4'}}
        pin_tauri_api(original)
        self.assertEqual(original['dependencies']['@tauri-apps/api'], TAURI_API_VERSION)

    def test_api_in_dev_dependencies_is_upgraded(self):
        pkg={'devDependencies': {'@tauri-apps/api': '^2.11.0'}}
        self.assertEqual(pin_tauri_api(pkg)['devDependencies']['@tauri-apps/api'], '2.12.3')

    def test_missing_api_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'Missing upstream @tauri-apps/api'):
            pin_tauri_api({'dependencies': {}})

    def test_minor_comparison_rejects_stale_api(self):
        self.assertNotEqual(major_minor('2.12.5'), major_minor('2.11.0'))
        self.assertEqual(major_minor('2.12.5'), major_minor('2.12.3'))

    def test_resolved_lock_guard_rejects_previous_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'src-tauri').mkdir()
            (root/'package.json').write_text(json.dumps({'dependencies': {'@tauri-apps/api':'2.12.3'}}),encoding='utf-8')
            (root/'package-lock.json').write_text(json.dumps({'packages':{
                'node_modules/@tauri-apps/api': {'version': '2.11.0'},
                'node_modules/@tauri-apps/cli': {'version': '2.12.4'}}}),encoding='utf-8')
            (root/'src-tauri/Cargo.lock').write_text('[[package]]\nname = "tauri"\nversion = "2.12.5"\n',encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'version lock mismatch'):
                check_versions(root)

    def test_resolved_lock_guard_accepts_compatible_versions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'src-tauri').mkdir()
            (root/'package.json').write_text(json.dumps({'dependencies': {'@tauri-apps/api':'2.12.3'}}),encoding='utf-8')
            (root/'package-lock.json').write_text(json.dumps({'packages':{
                'node_modules/@tauri-apps/api': {'version': '2.12.3'},
                'node_modules/@tauri-apps/cli': {'version': '2.12.4'}}}),encoding='utf-8')
            (root/'src-tauri/Cargo.lock').write_text('[[package]]\nname = "tauri"\nversion = "2.12.5"\n',encoding='utf-8')
            check_versions(root)

if __name__=='__main__':unittest.main()
