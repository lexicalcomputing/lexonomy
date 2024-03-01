#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import sqlite3
import unittest

sys.path.append('../')
from advance_search import result_id_list
from advance_search import get_query_parts
from advance_search import get_sql_query

current_dir = os.path.dirname(os.path.realpath(__file__))


# Unit tests
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(f'{current_dir}/../../data/dicts/test_import_nvh.sqlite')

    def test_key_exists(self):
        self.assertListEqual(result_id_list('sense', self.db), [1, 2, 3, 5])

    def test_key_not_exists(self):
        self.assertListEqual(result_id_list('sense#="0"', self.db), [4])

    # VALUES
    def test_value_equals(self):
        self.assertListEqual(result_id_list('sense="test_5"', self.db), [5])

    def test_value_not_equals(self):
        self.assertListEqual(result_id_list('sense!="test_5"', self.db), [1,2,3,4])

    def test_value_re_equals(self):
        self.assertListEqual(result_id_list('sense~="test_2.*"', self.db), [2])

    # COUNT
    def test_count_more_than(self):
        self.assertListEqual(result_id_list('s_example#>"0"', self.db), [1, 2, 3])

    def test_count_less_than(self):
        self.assertListEqual(result_id_list('image#<"2"', self.db), [1,2,3,4])

    def test_count_equals(self):
        self.assertListEqual(result_id_list('sense#="2"', self.db), [1,2])

    # OPERATORS
    def test_and_operator(self):
        self.assertListEqual(result_id_list('sense and flag="nok"', self.db), [3])

    def test_where_operator(self):
        self.assertListEqual(result_id_list('s_image#="1" where s_i_quality="bad"', self.db), [2])

    def test_where_operator_2(self):
        self.assertListEqual(result_id_list('i_quality="good" where i_license="general"', self.db), [3, 5])

    def test_where_operator_3(self):
        self.assertListEqual(result_id_list('i_quality="good" where i_license="general" where i_author="LCC"', self.db), [3, 5])
    
    def test_where_operator_4(self):
        # TODO the restriction on tree.fullpath is not enough need to somehow apply the count again
        self.assertListEqual(result_id_list('sense#="2" where (s_e_quality="good")', self.db), [1])

    def test_where_operator_with_or(self):
        self.assertListEqual(result_id_list('s_image#="1" where (s_i_quality="bad" or s_i_quality="low")', self.db), [2])

    def test_or_operator(self):
        self.assertListEqual(result_id_list('flag="nok" or flag="low_frq"', self.db), [3, 4, 5])

    def test_query_parse_1(self):
        query = 'sense~="my t*" where (flag="nok" or flag="offensive") where image'
        self.assertEqual(get_query_parts(query), [{'attr': 'sense', 'op': '~=', 'val': 'my t*'}, 'where', [{'attr': 'flag', 'op': '=', 'val': 'nok'}, 'or', {'attr': 'flag', 'op': '=', 'val': 'offensive'}], 'where', {'attr': 'image', 'op': None, 'val': None}])

    def test_query_parse_2(self):
        query = 'definition!="asda*" and (headword!="sads" and (example_translation!="akk"))'
        self.assertEqual(get_query_parts(query), [{'attr': 'definition', 'op': '!=', 'val': 'asda*'}, 'and', [{'attr': 'headword', 'op': '!=', 'val': 'sads'}, 'and', [{'attr': 'example_translation', 'op': '!=', 'val': 'akk'}]]])

    def test_query_parse_3(self):
        query = ' ( definition != "asda*"   and   (headword != "sads"   and  (   example_translation != "akk"  )  )    )  '
        self.assertEqual(get_query_parts(query), [[{'attr': 'definition', 'op': '!=', 'val': 'asda*'}, 'and', [{'attr': 'headword', 'op': '!=', 'val': 'sads'}, 'and', [{'attr': 'example_translation', 'op': '!=', 'val': 'akk'}]]]])
    
    def test_query_bad_query(self):
        try:
            result_id_list('headword="a" and headword="b" or headword="c"', self.db)
        except ValueError as e:
            self.assertEqual(str(e), 'More than one type of logic operator without any brackets')

if __name__ == '__main__':
    sys.stderr.write('SQLite version: ' + sqlite3.connect(':memory:').execute('SELECT sqlite_version();').fetchall()[0][0] + '\n')
    unittest.main()
