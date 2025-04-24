#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import json
from ops import getLocale
from icu import Locale, Collator
from ops import check_entry_completed

def condition2sql(condition, all_json_trees, tl_element, queried_trees=[]):
    key = condition['attr']
    value = condition['val']
    operator = condition['op']

    if operator == '#=' and value == '0':
        operator = 'not_exist'
    if not operator and not value:
        operator = 'exist'

    valkey = key
    if '_' in key:
        valkey = f'"{key}"'

    if key == tl_element:
        path = f'$."_value"'
    else:
        path = f'%."{valkey}"[_]."_value"' # TODO resolve support for 0-9 items

    sql = ''
    json_tree = all_json_trees.pop(0)
    key_not_exists = "(entries.id NOT IN (SELECT DISTINCT entries.id from entries, json_tree(entries.json) WHERE json_tree.key='" + key + "'))"

    if operator == '=':
        if key == '.*':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value REGEXP '\\b" + value + "\\b')"
        else:
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value = '" + value + "' AND " + json_tree + ".fullkey LIKE '" + path + "')"
    elif operator == '!=':
        if key == '.*':
            sql = "(entries.id NOT IN (SELECT DISTINCT entries.id from entries, json_tree(entries.json) WHERE json_tree.key='_value' AND json_tree.value REGEXP '\\b" + value + "\\b'))"
        else:
            sql = "((" + json_tree + ".key='_value' AND " + json_tree + ".value != '" + value + "' AND " + json_tree + ".fullkey LIKE '" + path + "') OR " + key_not_exists + ")"
    elif operator == 'exist':
        sql = "(" + json_tree + ".key='" + key + "')"
    elif operator == 'not_exist':
        sql = key_not_exists
    elif operator == '~=':
        if key == '.*':
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value REGEXP '" + value + "')"
        else:
            sql = "(" + json_tree + ".key='_value' AND " + json_tree + ".value REGEXP '" + value + "' AND " + json_tree + ".fullkey LIKE '" + path + "')"
    elif operator == '#=':
        sql = "(" + json_tree + ".key='" + key + "' AND json_array_length(" + json_tree + ".value)=" + value + ")"
    elif operator == '#>':
        sql = "(" + json_tree + ".key='" + key + "' AND json_array_length(" + json_tree + ".value)>" + value + ")"
    elif operator == '#<':
        sql = "((" + json_tree + ".key='" + key + "' AND json_array_length(" + json_tree + ".value)<" + value + ") OR " + key_not_exists + ")"

    queried_trees.append("SUBSTR(" + json_tree + ".key, 0, INSTR(" + json_tree + ".key, '" + valkey + "'))")
    return sql


def path_equal_check(queried_trees):
    t0, t1 = queried_trees[-2:]
    queried_trees.pop()
    return "(INSTR(" + t0 + "," + t1 + ") OR INSTR(" + t1 + "," + t0 + "))"


def lex_query2sql(query, all_json_trees, tl_element, queried_trees):
    if isinstance(query, list):
        if 'where' in query:
            sub_sql_1 = lex_query2sql(query[0], all_json_trees, tl_element, queried_trees)
            sub_sql_2 = lex_query2sql(query[2:], all_json_trees, tl_element, queried_trees)

            sql = '(' + sub_sql_1 + ' AND ' + sub_sql_2 + ' AND ' + path_equal_check(queried_trees) + ')'

        elif 'and' in query:
            sub_sql_1 = lex_query2sql(query[0], all_json_trees, tl_element, queried_trees)
            sub_sql_2 = lex_query2sql(query[2:], all_json_trees, tl_element, queried_trees)

            sql = '(' + sub_sql_1 + ' AND ' + sub_sql_2 + ')'
            queried_trees.pop() # only one tree to compare with outer condition

        elif 'or' in query:
            sub_sql_1 = lex_query2sql(query[0], all_json_trees, tl_element, queried_trees)
            sub_sql_2 = lex_query2sql(query[2:], all_json_trees, tl_element, queried_trees)

            sql = '(' + sub_sql_1 + ' OR ' + sub_sql_2 + ')' # TODO check if it can interfere with inclusive AND
            queried_trees.pop()

        elif len(query)==1 and isinstance(query[0], dict):
            sql = condition2sql(query[0], all_json_trees, tl_element, queried_trees)

        elif len(query)==1 and isinstance(query[0], list):
            sql = lex_query2sql(query[0], all_json_trees, tl_element, queried_trees)
        else:
            raise ValueError('ERROR: not correctly created query')
    else:
        sql = condition2sql(query, all_json_trees, tl_element, queried_trees)

    return sql


attr = '\s*(?P<attr>((?!=|!=|~=|#=|#>|#<| |\(|\)).)*)\s*'
operators='\s*(?P<op>=|!=|~=|#=|#>|#<)?\s*'
value = '\s*("(?P<val>((?!=|!=|~=|#=|#>|#<).)*)")?\s*'
and_or = '\s*(?P<lop>where|and|or)?\s*'
rest = '\s*(?P<rest>.*)?\s*'
left = '(?P<left>[ \(]*)?'
right = '(?P<right>[ \)]*)?'
query_split_re = re.compile('^' + left + attr + operators + value + right + and_or + rest + '$', re.IGNORECASE)

def split_query(text, tokens):
    match_result_dict = query_split_re.match(text).groupdict()

    # left bracket
    if match_result_dict.get('left', False):
        tokens += [x for x in match_result_dict['left'] if x != ' ']

    # attribute operator value
    condition = {'attr': None, 'op': None, 'val': None}
    for i in ['attr', 'op', 'val']:
        if match_result_dict.get(i, False):
            condition[i] = match_result_dict[i]
    tokens.append(condition)

    # right bracket
    if match_result_dict.get('right', False):
        tokens += [x for x in match_result_dict['right'] if x != ' ']

    # and/or operator
    if match_result_dict.get('lop', False):
        tokens.append(match_result_dict['lop'].lower())

    # rest
    if match_result_dict.get('rest', False):
        split_query(match_result_dict['rest'], tokens)


def get_query_parts(text):
    """
    Splits Lexonomy query into separate conditions and
    check correct bracketing (using stack automaton)
    """
    query_parts = []
    split_query(text, query_parts)

    # raise Value error if no brackets in complex query consisting of more than one operator
    if (len(set([x for x in query_parts if x in ['and', 'or', 'where']])) > 1) and not ('(' in query_parts or ')' in query_parts):
        raise ValueError('More than one type of logic operator without any brackets')

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


def add_json_trees(query_tokens, sql, all_json_trees, tree_id=1):
    """
    add the same number of JSON trees as the number of conditions
    joined by AND/OR operators, because each condition have to be
    evaluated on its own tree.
    """
    for item in query_tokens:
        if isinstance(item, list):
            tree_id = add_json_trees(item, sql, all_json_trees, tree_id)
        elif isinstance(item, str) and item in ['where', 'and', 'or']:
            sql.append(f',json_tree(entries.json) AS tree{tree_id} ')
            all_json_trees.append(f'tree{tree_id}')
            tree_id += 1
    return tree_id


def get_sql_query(query, tl_element, collate="", orderby="ASC", howmany=10, offset=0):
    """
    Transform Lexonomy query into SQL query
    query: str, query form Lexonomy
    """
    query_tokens = get_query_parts(query)
    sql = ["SELECT DISTINCT entries.id, entries.json, entries.nvh, entries.sortkey, entries.title FROM entries, json_tree(entries.json) AS tree0 "]
    all_json_trees = ['tree0']
    queried_trees = []
    add_json_trees(query_tokens, sql, all_json_trees)
    sql = ''.join(sql) + " WHERE " + lex_query2sql(query_tokens, all_json_trees, tl_element, queried_trees) + \
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

    c0 = dictDB.execute("SELECT json FROM configs WHERE id='titling'")
    r0 = c0.fetchone()
    sql_query = get_sql_query(query, json.loads(r0['json'])['headword'], collate, orderby, howmany, offset)
    dictDB.create_function("REGEXP", 2, regexp)
    # IMPORTANT INFO: we relay on uniqueness of attribute names
    c = dictDB.execute(sql_query)
    entries = []
    for entry in c.fetchall():
        item = {"id": entry["id"], "title": entry["title"], "sortkey": entry["sortkey"]}
        if fullNVH:
            item["nvh"] = entry["nvh"]
        if configs['progress_tracking'].get('tracked', False):
            item['is_completed'] = check_entry_completed(entry["nvh"], configs)
        entries.append(item)

    total = len(entries)
    return total, entries


def result_id_list(query, db):
    c0 = db.execute("SELECT json FROM configs WHERE id='titling'")
    r0 = c0.fetchone()
    sql_query = get_sql_query(query, json.loads(r0['json'])['headword'], howmany=1000)
    db.create_function("REGEXP", 2, regexp)
    c = db.execute(sql_query)
    return  [x[0] for x in c.fetchall()]
