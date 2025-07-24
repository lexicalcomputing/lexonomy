#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import copy
import json
import sqlite3
sys.path.insert(0, os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0])
from nvh import nvh


def getDB(dict_sqlite):
    conn = sqlite3.connect(dict_sqlite)
    conn.row_factory = sqlite3.Row
    conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on")
    return conn


def update_4_0(dictDB):
    new_formatting_structure = {"content": {"name": None,
                                            "path": None},
                                "styles": {},
                                "children": [],
                                "orientation": "column"}

    def transform_old_styling(old_node_styling):
        def update_styles(old_key, new_key, value_mapping, styles_subpart, new_node_formatting):
            if value_mapping:
                try:
                    value_mapping[old_node_styling[old_key]]
                except KeyError:
                    raise Exception(f'ERROR: Value mapping for {old_node_styling[old_key]} not present in {old_node_styling}!')

                if new_node_formatting.get(styles_subpart):
                    if isinstance(value_mapping[old_node_styling[old_key]], dict):
                        for key, value in value_mapping[old_node_styling[old_key]].items():
                            new_node_formatting[styles_subpart][key] = value
                    else:
                        new_node_formatting[styles_subpart][new_key] = value_mapping[old_node_styling[old_key]]
                else:
                    if isinstance(value_mapping[old_node_styling[old_key]], dict):
                        new_node_formatting[styles_subpart] = value_mapping[old_node_styling[old_key]]
                    else:
                        new_node_formatting[styles_subpart] = {new_key: value_mapping[old_node_styling[old_key]]}
            else:
                # if there is no mapping use original value
                if new_node_formatting.get(styles_subpart):
                    new_node_formatting[styles_subpart][new_key] = old_node_styling[old_key]
                else:
                    new_node_formatting[styles_subpart] = {new_key: old_node_styling[old_key]}

        new_node_formatting = {}
        # ================
        # TEXTSIZE
        # ================
        if old_node_styling.get('textsize'):
            value_mapping = {1: 12, 2: 16, 3: 19,
                             4: 24, 5: 32, 6: 40}
            update_styles('textsize', 'font-size', value_mapping, 'element', new_node_formatting)
        # ================
        # borderRadius
        # ================
        if old_node_styling.get('borderRadius'):
            value_mapping = {'small': 5,
                             'medium': 10,
                             'large': 15
                             }
            update_styles('borderRadius', 'border-radius', value_mapping, 'element', new_node_formatting)
        # ================
        # background
        # ================
        if old_node_styling.get('background'):
            value_mapping = {'yellow': '#fffde7',
                             'blue': '#E3F2FD',
                             'grey': '#757575'
                             }
            update_styles('background', 'background-color', value_mapping, 'element', new_node_formatting)
        # ================
        # colour
        # ================
        if old_node_styling.get('colour'):
            value_mapping = {'red': '#c62132',
                             'blue': '#0277bd',
                             'green': '#388e3c',
                             'grey': '#757575'
                             }
            update_styles('colour', 'color', value_mapping, 'element', new_node_formatting)
        # ================
        # slant
        # ================
        if old_node_styling.get('slant'):
            update_styles('slant', 'font-style', None, 'element', new_node_formatting)
        # ================
        # weight
        # ================
        if old_node_styling.get('weight'):
            update_styles('weight', 'font-weight', None, 'element', new_node_formatting)
        # ================
        # direction
        # ================
        if old_node_styling.get('direction'):
            update_styles('direction', 'direction', None, 'element', new_node_formatting)
        # ================
        # innerPunc
        # ================
        if old_node_styling.get('innerPunc'):
            value_mapping = {"roundBrackets":  {"leftPunc": "(", "rightPunc": ")"},
                             "squareBrackets": {"leftPunc": "[", "rightPunc": "]"},
                             "curlyBrackets":  {"leftPunc": "{", "rightPunc": "}"},
                             "comma": {"leftPunc": "", "rightPunc": ","},
                             "dot": {"leftPunc": "", "rightPunc": "."},
                             "semicolon": {"leftPunc": "", "rightPunc": ";"},
                             "colon": {"leftPunc": "", "rightPunc": ","}
                            }
            update_styles('innerPunc', '', value_mapping, 'element', new_node_formatting)
        # ================
        # outerPunc
        # ================
        if old_node_styling.get('outerPunc'):
            value_mapping = {"roundBrackets":  {"leftPunc": "(", "rightPunc": ")"},
                             "squareBrackets": {"leftPunc": "[", "rightPunc": "]"},
                             "curlyBrackets":  {"leftPunc": "{", "rightPunc": "}"},
                             "comma": {"leftPunc": "", "rightPunc": ","},
                             "dot": {"leftPunc": "", "rightPunc": "."},
                             "semicolon": {"leftPunc": "", "rightPunc": ";"},
                             "colon": {"leftPunc": "", "rightPunc": ","}
                            }
            update_styles('outerPunc', '', value_mapping, 'element', new_node_formatting)
        # ================
        # BORDER
        # ================
        if old_node_styling.get('border'):
            value_mapping = {'solid': {'border': 'solid', 'border-color': '#808080', 'border-width': 1},
                             'thick': {'border': 'solid', 'border-color': '#808080', 'border-width': 2},
                             'dotted': {'border': 'dotted', 'border-color': '#808080', 'border-width': 1}}
            update_styles('border', '', value_mapping, 'element', new_node_formatting)
        # ================
        # gutter
        # ================
        gutter = old_node_styling.get('gutter')
        if gutter:
            if gutter == "indent":
                new_node_formatting["element"]["margin-left"] = "20"
            else:
                value_mapping = {'sensenum0': {"bullet-use-numbers": True},
                                 'sensenum1': {"bullet-use-numbers": True},
                                 'sensenum2': {"bullet-use-numbers": True},
                                 'sensenum3': {"bullet-use-numbers": True},
                                 'disk': {"bullet-set-bullet": "•", "bullet-use-bullets": True, "bullet-use-numbers": False},
                                 'square': {"bullet-set-bullet": "■", "bullet-use-bullets": True, "bullet-use-numbers": False},
                                 'diamond': {"bullet-set-bullet": "◆", "bullet-use-bullets": True, "bullet-use-numbers": False},
                                 'arrow': {"bullet-set-bullet": "→", "bullet-use-bullets": True, "bullet-use-numbers": False}
                                 }
                update_styles('gutter', '', value_mapping, 'bullet', new_node_formatting)
        # ================
        # indentAll
        # ================
        if old_node_styling.get('indentAll'):
            update_styles('indentAll', 'bullet-use-with-single-item', None, 'bullet', new_node_formatting)
        # ================
        # label
        # ================
        if old_node_styling.get('label'):
            update_styles('label', 'label-text-value', None, 'label', new_node_formatting)

        return new_node_formatting

    def get_recur_children(node_path, structure_elements, formatting, hidden_elements):
        node_name = node_path.rsplit('.', 1)[-1]
        children = structure_elements[node_path].get('children', [])
        styles = transform_old_styling(formatting.get('elements', {}).get(node_path, {}))
        styles.setdefault('element', {})
        new_node_formatting = copy.deepcopy(new_formatting_structure)
        new_node_formatting['content']['name'] = node_name
        new_node_formatting['content']['path'] = node_path

        if not children:
            new_node_formatting['styles'] = styles
        else:
            # element has children so it is an element group. We need to add an actual element value and its children
            value_node = copy.deepcopy(new_formatting_structure)

            value_node['styles'] = styles
            new_node_formatting['styles'].setdefault('element', {})
            # styles which should be applied to the group not the actual element (e.g. sense group, not sense)
            for key in ["border", "border-color", "border-width", "border-radius", "background-color", "margin-left"]:
                if key in styles['element']:
                    new_node_formatting['styles']['element'][key] = styles['element'][key]
                    del value_node['styles']['element'][key]
            new_node_formatting['children'].append(value_node)
            value_node['content']['name'] = node_name
            value_node['content']['path'] = node_path

            for child_path in children:
                # ====================
                # MARKUP FROM CHILDREN
                if structure_elements[child_path].get('type', 'string') == 'markup':
                    value_node['styles'].setdefault('markup', {})
                    value_node['styles']['markup'][child_path] = transform_old_styling(formatting.get('elements', {}).get(child_path, {})).get('element')
                # ====================
                else:
                    if child_path not in hidden_elements:
                        new_node_formatting['children'].append(get_recur_children(child_path, structure_elements, formatting, hidden_elements))
        return new_node_formatting

    def update_formatting(structure_elements, root, formatting):
        hidden_elements = [key for key, value in formatting.get('elements', {}).items() if value.get("hidden", False) == True]

        return get_recur_children(root, structure_elements, formatting, hidden_elements)


    formatting = {}
    r = dictDB.execute("SELECT json FROM configs WHERE id='formatting'")
    if r:
        formatting = json.loads(r.fetchone()['json'])

    structure = json.loads(dictDB.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
    root = nvh.schema_get_root_name(structure['nvhSchema'])
    desktop_layout = update_formatting(nvh.schema_nvh2json(structure['nvhSchema']), root, formatting)

    other_layout = copy.deepcopy(new_formatting_structure)
    other_layout['content']['name'] = root
    other_layout['content']['path'] = root

    formatting['layout'] = {'desktop': {'schema': desktop_layout,
                                        "configured": True},
                            'tablet': {'schema': other_layout,
                                        "configured": False},
                            'mobile': {'schema': other_layout,
                                        "configured": False},
                            'pdf': {'schema': other_layout,
                                        "configured": False}}

    # del formatting['elements']        
    # dictDB.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ('formatting', json.dumps(formatting)))
    # dictDB.commit()
    print(json.dumps(formatting, indent=2))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('dict', type=str,
                        help='Dict sqlite file')
    args = parser.parse_args()

    dictDB = getDB(args.dict)
    update_4_0(dictDB)

if __name__ == '__main__':
    main()
