#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import re
import sys
import sqlite3
import unittest
current_dir = os.path.dirname(os.path.realpath(__file__))

def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None

def query2sqliteToken(token):
    match token:
        case _ if '!=' in token:
            # !=
            parts = token.split('!=')
            operator = '!='
            path = parts[0]
            value = parts[1]
        case _ if '~=' in token:
            #regex
            parts = token.split('~=')
            operator = '~='
            path = parts[0]
            value = parts[1]
        case _ if '#=' in token:
            #count
            parts = token.split('#=')
            operator = '#='
            path = parts[0]
            value = parts[1]
        case _ if '#>' in token:
            #count
            parts = token.split('#>')
            operator = '#>'
            path = parts[0]
            value = parts[1]
        case _ if '#<' in token:
            #count
            parts = token.split('#<')
            operator = '#<'
            path = parts[0]
            value = parts[1]
        case _ if '=' in token:
            # =
            parts = token.split('=')
            operator = '='
            path = parts[0]
            value = parts[1]
        case _:
            operator = 'exist'
            path = token.strip()
            value = ''

    fullpath = path.replace('.', '[%].')
    fullpathval = '$.' + fullpath + '[%]._value'

    sql = ''
    match operator:
        case '=':
            sql = "(json_tree.key='_value' AND json_tree.value = '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case '!=':
            sql = "(json_tree.key='_value' AND json_tree.value != '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case 'exist':
            sql = "(json_tree.fullkey LIKE '$." + fullpath + "[%]')"
        case '~=':
            sql = "(json_tree.key='_value' AND json_tree.value REGEXP '" + value + "' AND json_tree.fullkey LIKE '" + fullpathval + "')"
        case '#=':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.fullkey LIKE '$." + fullpath + "[%]' GROUP BY entries.id HAVING COUNT(json_tree.key)=" + value + "))"
        case '#>':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.fullkey LIKE '$." + fullpath + "[%]' GROUP BY entries.id HAVING COUNT(json_tree.key)>" + value + "))"
        case '#<':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.fullkey LIKE '$." + fullpath + "[%]' GROUP BY entries.id HAVING COUNT(json_tree.key)<" + value + "))"
    return sql


def query2sqliteQuery(query_list):
    result_list = []
    for token in query_list:
        if type(token) == list:
            result_list.append(query2sqliteQuery(token))
        else:
            if token == 'and' or token == 'or':
                result_list.append(token)
            else:
                result_list.append(query2sqliteToken(token))
    return '(' + ' '.join(result_list) + ')'


def parse_nested(text, left=r'[(]', right=r'[)]', sep=r' '):
    pat = r'({}|{}|{})'.format(left, right, sep)
    
    tokens = re.split(pat, text)
    # print(tokens)
    # sys.exit()
    stack = [[]]
    for x in tokens:
        if not x or re.match(sep, x): continue
        if re.match(left, x):
            stack[-1].append([])
            stack.append(stack[-1][-1])
        elif re.match(right, x):
            stack.pop()
            if not stack:
                raise ValueError('error: opening bracket is missing')
        else:
            stack[-1].append(x)
    if len(stack) > 1:
        print(stack)
        raise ValueError('error: closing bracket is missing')
    return stack.pop()


def dql2sqlite(query):
    parsed_query = parse_nested(query)
    # distinct - different
    # json_tree - table-valued function that walks the JSON value provided as its first argument and returns a table consisting of one row for each array element or object member
    # TODO change
    sql = "select distinct entries.id, entries.json from entries, json_tree(entries.json) where " + query2sqliteQuery(parsed_query) + " limit 10;"
    return sql


def get_entries(query, db):
    db.create_function("REGEXP", 2, regexp)
    c = db.execute(query)
    for r in c.fetchall():
        yield(r)


def result_id_list(query, db):
    db.create_function("REGEXP", 2, regexp)
    c = db.execute(query)
    return  [x[0] for x in c.fetchall()]
        

# Unit tests
class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(f'{current_dir}/tests/test.sqlite')

    def test_key_exists(self):
        query = dql2sqlite('entry.hw.sense')
        self.assertListEqual(result_id_list(query, self.db), [1, 2, 3, 5])

    # VALUES
    def test_value_equals(self): # OK
        query = dql2sqlite('entry.hw.sense=test_5')
        self.assertListEqual(result_id_list(query, self.db), [5])

    def test_value_re_equals(self):
        query = dql2sqlite('entry.hw.sense~=test_2.*')
        self.assertListEqual(result_id_list(query, self.db), [2])
    
    # COUNT
    def test_count_more_than(self): # OK
        query = dql2sqlite('entry.hw.sense.example#>0')
        self.assertListEqual(result_id_list(query, self.db), [1, 2, 3])

    def test_count_less_than(self):
        query = dql2sqlite('entry.hw.sense.image#<0')
        self.assertListEqual(result_id_list(query, self.db), [1, 2, 3, 4])
    
    def test_count_equals(self):
        query = dql2sqlite('entry.hw.sense#=0')
        self.assertListEqual(result_id_list(query, self.db), [4])

    # def test_count_condition(self):
    #     query = dql2sqlite('entry.hw.sense.example#>0.quality=bad')
    #     self.assertListEqual(result_id_list(query, self.db), [4])

    # OPERATORS
    def test_and_operator(self):
        query = dql2sqlite('entry.hw.sense and entry.hw.flag=nok')
        self.assertListEqual(result_id_list(query, self.db), [3])

    def test_or_operator(self):
        query = dql2sqlite('entry.hw.flag=nok or entry.hw.flag=low_frq')
        self.assertListEqual(result_id_list(query, self.db), [3, 4, 5])


if __name__ == '__main__':
    unittest.main()
    # main()