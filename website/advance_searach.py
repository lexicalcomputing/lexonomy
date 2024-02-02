#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import re
import sqlite3
import unittest
from ops import getLocale
from icu import Locale, Collator
current_dir = os.path.dirname(os.path.realpath(__file__))


def query2sqliteToken(condition):
    path = condition['attr']
    value = condition['val']
    operator = condition['op']

    if operator == '#=' and value == '0':
        operator = 'not_exist'
    if not operator and not value:
        operator = 'exist'
    
    if '_' in path:
        fullpath = '$.%.' + '"' + path + '"'
    else:
        fullpath = '$.%.' + path

    fullpathval = fullpath + '[%]' + '."_value"'
    sql = ''
    json_tree = 'json_tree'
    
    match operator:
        case '=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value = '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case '!=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value != '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case 'exist':
            sql = "(" + json_tree + ".fullkey LIKE '" + fullpath + '[%]' + "')"
        case 'not_exist':
            sql = "entries.id NOT IN (SELECT DISTINCT entries.id from entries, json_tree(entries.json) where (json_tree.fullkey LIKE '" + fullpathval + "'))"
        case '~=':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value REGEXP '" + value + "' AND " + json_tree + ".fullkey LIKE '" + fullpathval + "')"
        case '#=':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)=" + value + "))"
        case '#>':
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)>" + value + "))"
        case '#<':
            # second part for count=0 (asks if attribute exists)
            sql = "(entries.id IN (SELECT entries.id FROM entries,json_tree(entries.json) WHERE json_tree.path LIKE '" + fullpath + "' GROUP BY entries.id HAVING COUNT(json_tree.key)<" + value + "))" + \
                  " or (entries.id NOT IN (SELECT DISTINCT entries.id from entries, json_tree(entries.json) where (json_tree.fullkey LIKE '" + fullpathval + "')))"
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


attr = '(?P<attr>((?!=|!=|~=|#=|#>|#<| |\(|\)).)*)'
operators='(?P<op>=|!=|~=|#=|#>|#<)?'
value = '("(?P<val>((?!=|!=|~=|#=|#>|#<).)*)")?'
and_or = '(\s*(?P<lop>and|or)\s*)?'
rest = '(?P<rest>.*)?'
left = '(?P<left>\(*)?'
right = '(?P<right>\)*)?'
query_split_re = re.compile('^' + left + attr + operators + value + right + and_or + rest + '$')

def split_query(text, tokens):
    match_result_dict = query_split_re.match(text).groupdict()

    # left bracket
    if match_result_dict.get('left', False):
        tokens += [x for x in match_result_dict['left']]

    # attribute operator value
    condition = {'attr': None, 'op': None, 'val': None}
    for i in ['attr', 'op', 'val']:
        if match_result_dict.get(i, False):
            condition[i] = match_result_dict[i]
    tokens.append(condition)

    # right bracket
    if match_result_dict.get('right', False):
        tokens += [x for x in match_result_dict['right']]

    # and/or operator
    if match_result_dict.get('lop', False):
        tokens.append(match_result_dict['lop'])
    
    # rest
    if match_result_dict.get('rest', False):
        if re.match('^[()]*$', match_result_dict['rest']):
            condition.append(match_result_dict['rest'])
        else:
            split_query(match_result_dict['rest'], tokens)
    

def get_query_parts(text):
    query_parts = []
    split_query(text, query_parts)

    stack = [[]]
    for x in query_parts:
        if isinstance(x, str) and re.match(r'[(]', x):
            stack[-1].append([])
            stack.append(stack[-1][-1])
        elif isinstance(x, str) and re.match(r'[)]', x):
            stack.pop()
            if not stack:
                raise ValueError('ERROR: Opening bracket is missing in advance query!')
        else:
            stack[-1].append(x)
    if len(stack) > 1:
        raise ValueError('ERROR: Closing bracket is missing in advance query!')
    return stack.pop()


def nvh_query2sql_query(query, collate="", orderby="ASC", howmany=10, offset=0):
    query_tokens = get_query_parts(query)
    sql = "SELECT DISTINCT entries.id, entries.json, entries.nvh, entries.sortkey, entries.title FROM entries, json_tree(entries.json) WHERE " + \
            query2sqliteQuery(query_tokens) + \
            " ORDER BY entries.sortkey " + collate + " " + orderby + " LIMIT " + str(howmany) + " OFFSET " + str(offset) + ";" 
    return sql


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def getEntries(dictDB, configs, query="", howmany=10, offset=0, sortdesc=False, reverse=False, fullNVH=False):
    collate = ""
    if "locale" in configs["titling"]:
        collator = Collator.createInstance(Locale(getLocale(configs)))
        dictDB.create_collation("custom", collator.compare)
        collate = "collate custom"

    if reverse:
        sortdesc = not sortdesc
    orderby = "ASC"
    if sortdesc:
        orderby = "DESC"

    sql_query = nvh_query2sql_query(query, collate, orderby, howmany, offset)
    dictDB.create_function("REGEXP", 2, regexp)
    # IMPORTANT INFO: we relay on uniqueness of attribute names
    c = dictDB.execute(sql_query)
    entries = []
    for entry in c.fetchall():
        item = {"id": entry["id"], "title": entry["title"], "sortkey": entry["sortkey"]}
        # TODO flagging
        if fullNVH:
            item["nvh"] = entry["nvh"]
        entries.append(item)

    total = len(entries)
    return total, entries, False


def result_id_list(query, db):
    sql_query = nvh_query2sql_query(query, howmany=1000)
    db.create_function("REGEXP", 2, regexp)
    c = db.execute(sql_query)
    return  [x[0] for x in c.fetchall()]
        

# Unit tests
class TestQueries(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(f'{current_dir}/tests/test.sqlite')

    def test_key_exists(self): # OK
        self.assertListEqual(result_id_list('sense', self.db), [1, 2, 3, 5])

    # VALUES
    def test_value_equals(self): # OK
        self.assertListEqual(result_id_list('sense="test_5"', self.db), [5])

    def test_value_re_equals(self): # OK
        self.assertListEqual(result_id_list('sense~="test_2.*"', self.db), [2])
    
    # COUNT
    def test_count_more_than(self):
        self.assertListEqual(result_id_list('s_example#>"0"', self.db), [1, 2, 3])

    def test_count_less_than(self):
        self.assertListEqual(result_id_list('image#<"2"', self.db), [1,2,3,4])
    
    def test_count_equals(self):
        self.assertListEqual(result_id_list('sense#="0"', self.db), [4])

    # def test_count_condition(self): # TODO
    #     self.assertListEqual(result_id_list('example#>0.quality=bad', self.db), [4])

    # OPERATORS
    def test_and_operator(self):
        self.assertListEqual(result_id_list('sense and flag="nok"', self.db), [3])

    def test_or_operator(self):
        self.assertListEqual(result_id_list('flag="nok" or flag="low_frq"', self.db), [3, 4, 5])

    def test_query_format(self):
        query = '(sense~="my t*" and (flag="nok" or flag="offensive") and image)'
        print(get_query_parts(query))
        print(nvh_query2sql_query(query))


if __name__ == '__main__':
    print('SQLite version: ' + sqlite3.connect(':memory:').execute('SELECT sqlite_version();').fetchall()[0][0])
    unittest.main()
