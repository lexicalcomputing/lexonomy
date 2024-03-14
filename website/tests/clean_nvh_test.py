#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import sys
import unittest
import fileinput

sys.path.append('../')
from nvh import nvh


# Unit tests
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.import_nvh = nvh.parse_file(fileinput.input('example_nvh/to_clean.nvh'))

    def test_rm_duplicates(self):
        clean_log = []
        self.import_nvh.clean_duplicate_nodes(log=clean_log)
        self.assertListEqual(clean_log, ['removing duplicate node image: to_remove',
                                         'removing duplicate node notes: to_remove'])

    def test_rename(self):
        rename_dict = {}
        rename_log = []
        self.import_nvh.rename_nodes(rename_dict, log=rename_log)
        self.assertListEqual(rename_log, ['renaming node name to preserve uniqueness lemma -> sense_lemma',
                                          'renaming node name to preserve uniqueness flag -> image_flag',
                                          'renaming node name to preserve uniqueness quality -> example_quality',
                                          'renaming node name to preserve uniqueness source -> lang_source',
                                          'renaming node name to preserve uniqueness flag -> lang_flag'])

if __name__ == '__main__':
    unittest.main()
