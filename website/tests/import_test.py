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


def transform(import_file):
    supported_formats = re.compile('^.*\.(xml|nvh)$', re.IGNORECASE)
    if supported_formats.match(import_file):
        try:
            if import_file.endswith('.xml'):
                # XML file transforamtion
                input_nvh = ops.xml2nvh(import_file)
                dictionary, schema = ops.nvh_dict_schema(input_nvh)
                with open(import_file + ".xml2nvh.nvh", 'w') as f:
                    dictionary.dump(f)
                
            elif import_file.endswith('.nvh'):
                dictionary, schema = ops.nvh_dict_schema(fileinput.input([import_file]))

        except ValueError as e:
            return {"msg": "", "success": False, "error": e, "url": 'test_import_xml'}                
    else:
        return{"success": False, "url": 'test_import_xml', 
                "error": 'Unsupported format for import file. An .xml or .nvh file are required.', 'msg': ''}
    return schema

# Unit tests
class TestQueries(unittest.TestCase):
    
    def test_xml_import(self):
        import_file = current_dir + '/test_import.xml'
        schema = transform(import_file)
        res, msg, error = ops.makeDict('test_import_xml', None, 'test_import_xml', "", 'test_import_xml@lexonomy.com', 
                                        None, import_file + ".xml2nvh.nvh", 'HWD', schema)
        self.assertEqual(error, '')
        self.assertEqual(res, True)
        time.sleep(5)
        with open(import_file + ".xml2nvh.nvh.err", 'r') as f:
            err_content = f.read()
        self.assertEqual(err_content, '')


    def test_nvh_import(self):
        import_file = current_dir + '/test_import.nvh'
        schema = transform(import_file)
        res, msg, error = ops.makeDict('test_import_nvh', None, 'test_import_nvh', "", 'test_import_nvh@lexonomy.com', 
                                        None, import_file, 'HWD', schema)
        self.assertEqual(error, '')
        self.assertEqual(res, True)
        time.sleep(5)
        with open(import_file + ".err", 'r') as f:
            err_content = f.read()
        self.assertEqual(err_content, '')


if __name__ == '__main__':
    unittest.main()
