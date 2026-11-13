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
from patch_source import replace_once, replace_regex


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

class BinaryTests(unittest.TestCase):
    def test_reject_dummy_mz(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'fake.exe'; f.write_bytes(b'MZ'+b'\0'*254)
            with self.assertRaises(RuntimeError):pe_machine(f)

if __name__=='__main__':unittest.main()
