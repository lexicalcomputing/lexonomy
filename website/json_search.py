#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import re
import sys
import pysqlite3 as sqlite3
import unittest
current_dir = os.path.dirname(os.path.realpath(__file__))


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def query2sqliteToken(token, all_json_trees):
    match token:
        case _ if '!=' in token:
            # !=
            parts = token.split('!=')
            path = parts[0]
            value = parts[1]
            operator = '!='
        case _ if '~=' in token:
            #regex
            parts = token.split('~=')
            path = parts[0]
            value = parts[1]
            operator = '~='
        case _ if '#=' in token:
            #count
            parts = token.split('#=')
            path = parts[0]
            value = parts[1]
            if value == '0':
                operator = 'not_exist'
            else:
                operator = '#='
        case _ if '#>' in token:
            #count
            parts = token.split('#>')
            path = parts[0]
            value = parts[1]
            operator = '#>'
        case _ if '#<' in token:
            #count
            parts = token.split('#<')
            path = parts[0]
            value = parts[1]
            if value == '1':
                operator = 'not_exist'
            else:
                operator = '#<'
        case _ if '=' in token:
            # =
            parts = token.split('=')
            path = parts[0]
            value = parts[1]
            operator = '='
        case _:
            path = token.strip()
            value = ''
            operator = 'exist'
    
    if '_' in path:
        fullpath = '$.%.' + '"' + path + '"'
    else:
        fullpath = '$.%.' + path

    fullpathval = fullpath + '[%]' + '."_value"'

    sql = ''

    # for and/or queries
    json_tree = 'json_tree'
    if all_json_trees:
        json_tree = all_json_trees.pop(0)

    match operator:
        case '=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value = '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case '!=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value != '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case 'exist':
            sql = "(" + json_tree + ".fullkey LIKE '" + fullpath + '[%]' + "')"
        case 'not_exist':
            sql = "entries.id NOT IN (SELECT DISTINCT entries.id from entries, " + json_tree + "(entries.json) where (" + json_tree + ".fullkey LIKE '" + fullpathval + "'))"
        case '~=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value REGEXP '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case '#=':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)=" + value + "))"
        case '#>':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)>" + value + "))"
        case '#<':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)<" + value + "))"
    return sql


def query2sqliteQuery(query_list, all_json_trees):
    result_list = []
    for token in query_list:
        if type(token) == list:
            result_list.append(query2sqliteQuery(token, all_json_trees))
        else:
            if token == 'and' or token == 'or':
                result_list.append(token)
            else:
                result_list.append(query2sqliteToken(token, all_json_trees))
    return '(' + ' '.join(result_list) + ')'


def get_query_tokens(text, left=r'[(]', right=r'[)]', sep=r' '):
    pat = r'({}|{}|{})'.format(left, right, sep)
    
    tokens = re.split(pat, text)
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
        raise ValueError('error: closing bracket is missing')
    return stack.pop()


def dql2sqlite(query):
    def make_json_trees(query_tokens, sql, tree_id, all_json_trees):
        for item in query_tokens:
            if isinstance(item, list):
                tree_id = make_json_trees(item, sql, tree_id, all_json_trees)
            elif isinstance(item, str) and item not in ['and', 'or']:
                sql.append(f',json_tree(entries.json) AS tree{tree_id} ')
                all_json_trees.append(f'tree{tree_id}')
                tree_id += 1
        return tree_id

    query_tokens = get_query_tokens(query)
    all_json_trees = []
    if 'and' in query_tokens or 'or' in query_tokens:
        # Need to perform each condition on own json_tree
        # select distinct entries.id, entries.json from entries, json_tree(entries.json) AS sense,  json_tree(entries.json) AS flag 
        # where ((sense.fullkey LIKE '$.%.sense[%]') and 
        # (flag.key='_value' AND flag.value = 'nok' AND flag.fullkey LIKE '$.%.flag[%]._value')) limit 10;
        sql = ["SELECT DISTINCT entries.id, entries.json FROM entries"]
        make_json_trees(query_tokens, sql, 0, all_json_trees)
        sql = ''.join(sql) + " where " + query2sqliteQuery(query_tokens, all_json_trees) + " limit 10;"
    else:
        sql = "SELECT DISTINCT entries.id, entries.json FROM entries, json_tree(entries.json) WHERE " + query2sqliteQuery(query_tokens, all_json_trees) + " limit 10;"
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
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(f'{current_dir}/tests/test.sqlite')

    def test_key_exists(self): # OK
        query = dql2sqlite('sense')
        self.assertListEqual(result_id_list(query, self.db), [1, 2, 3, 5])

    # VALUES
    def test_value_equals(self): # OK
        query = dql2sqlite('sense=test_5')
        self.assertListEqual(result_id_list(query, self.db), [5])

    def test_value_re_equals(self): # OK
        query = dql2sqlite('sense~=test_2.*')
        self.assertListEqual(result_id_list(query, self.db), [2])
    
    # COUNT
    def test_count_more_than(self):
        query = dql2sqlite('sense_example#>0')
        self.assertListEqual(result_id_list(query, self.db), [1, 2, 3])

    def test_count_less_than(self):
        query = dql2sqlite('image#<2')
        self.assertListEqual(result_id_list(query, self.db), [3])
    
    def test_count_equals(self):
        query = dql2sqlite('sense#=0')
        self.assertListEqual(result_id_list(query, self.db), [4])

    # def test_count_condition(self): # TODO
    #     query = dql2sqlite('example#>0.quality=bad')
    #     self.assertListEqual(result_id_list(query, self.db), [4])

    # OPERATORS
    def test_and_operator(self):
        query = dql2sqlite('sense and flag=nok')
        self.assertListEqual(result_id_list(query, self.db), [3])

    def test_or_operator(self):
        query = dql2sqlite('flag=nok or flag=low_frq')
        self.assertListEqual(result_id_list(query, self.db), [3, 4, 5])


if __name__ == '__main__':
    print('SQLite version: ' + sqlite3.connect(':memory:').execute('SELECT sqlite_version();').fetchall()[0][0])
    unittest.main()