#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import io
import sys
import unittest
import fileinput

sys.path.append('../')
from nvh import nvh


# Unit tests
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.import_nvh = nvh.parse_file(fileinput.input('example_nvh/to_clean.nvh', encoding="utf-8"))

    def test_rm_duplicates(self):
        log = io.StringIO()
        self.import_nvh.clean_duplicate_nodes(out=log)
        log.seek(0)
        self.assertEqual(log.read(), 'WARNING: removing duplicate node image: to_remove\n'
                                     'WARNING: removing duplicate node notes: to_remove\n')

    def test_rename(self):
        rename_dict = {}
        log = io.StringIO()
        self.import_nvh.rename_nodes(rename_dict, out=log)
        log.seek(0)
        self.assertEqual(log.read(), 'WARNING: renaming node name to preserve uniqueness lemma -> sense_lemma\n'
                                     'WARNING: renaming node name to preserve uniqueness flag -> image_flag\n'
                                     'WARNING: renaming node name to preserve uniqueness quality -> example_quality\n'
                                     'WARNING: renaming node name to preserve uniqueness source -> lang_source\n'
                                     'WARNING: renaming node name to preserve uniqueness flag -> lang_flag\n')

if __name__ == '__main__':
    unittest.main()
