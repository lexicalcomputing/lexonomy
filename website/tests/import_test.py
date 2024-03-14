#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import os
import sys
import unittest
import time
import fileinput

sys.path.append('../')
import ops

current_dir = os.path.dirname(os.path.realpath(__file__))
supported_formats = re.compile('^.*\.(xml|nvh)$', re.IGNORECASE)


# Unit tests
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.error_re = re.compile('(^|.*\n)ERROR.*', re.IGNORECASE)
    
    def test_xml_import(self):
        import_file = current_dir + '/test_import.xml'
        res, msg, error = ops.makeDict('test_import_xml', None, 'test_import_xml', "", 'test_import_xml@lexonomy.com', 
                                        None, import_file, 'HWD')
        self.assertEqual(error, [])
        self.assertEqual(res, True)
        time.sleep(5)
        with open(import_file + ".log", 'r') as f:
            err_content = f.read()
        self.assertFalse(self.error_re.match(err_content))


    def test_nvh_import(self): 
        import_file = current_dir + '/test_import.nvh'
        res, msg, error = ops.makeDict('test_import_nvh', None, 'test_import_nvh', "", 'test_import_nvh@lexonomy.com', 
                                        None, import_file, 'hw')
        self.assertEqual(error, [])
        self.assertEqual(res, True)
        time.sleep(5)
        with open(import_file + ".log", 'r') as f:
            err_content = f.read()
        self.assertFalse(self.error_re.match(err_content))

    def test_dante_import(self):
        import_file = current_dir + '/dante.xml'
        res, msg, error = ops.makeDict('test_import_dante', None, 'test_import_dante', "", 'test_import_dante@lexonomy.com', 
                                        None, import_file, 'HWD')
        self.assertEqual(error, [])
        self.assertEqual(res, True)
        time.sleep(1200)
        with open(import_file + ".log", 'r') as f:
            err_content = f.read()
        self.assertFalse(self.error_re.match(err_content))


if __name__ == '__main__':
    unittest.main()
