#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ

# ============================
# READ BEFORE NEW UPDATE
# ============================
# To add a new update to a lexonomy database or dict database add 
# new update number in mainDB_updates or dictDB_updates and create 
# method in Updates class with name "update_<update_number>"
# ============================

import os
import re
import sys
import stat
import copy
import json
import random
import string
import shutil
import sqlite3
import hashlib
from datetime import datetime

# WARNING the mainDB_updates versions and dictDB_updates updates cannot have same numbers
# The new update need to have verion number greater than sorted(mainDB_updates + dictDB_updates)
mainDB_updates = ['3.24']
dictDB_updates = ['2.153', '3.0', '3.1', '3.2', '3.31', '4.0']
DBupdates = sorted(mainDB_updates + dictDB_updates)
if set(mainDB_updates) & set(dictDB_updates):
    sys.stderr.write('ERROR: Main DB and Dict DB updates bare same version number. Please make sure they differ.\n')
    sys.exit()

timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

sys.path.insert(0, os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0])
import ops
from nvh import nvh
main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def to_absolute(path_to_resolve):
    if os.path.isabs(path_to_resolve):
        abs_path = os.path.normpath(path_to_resolve)
    else:
        abs_path = os.path.normpath(os.path.join(main_dir, path_to_resolve))
    return abs_path

# copy siteconfig.json/config.js from template if needed
if not os.path.exists(os.path.join(main_dir, "config.js")):
    shutil.copy(os.path.join(main_dir, "config.js.template"), os.path.join(main_dir, "config.js"))
if not os.path.exists(os.path.join(main_dir, "siteconfig.json")):
    shutil.copy(os.path.join(main_dir, "siteconfig.json.template"), os.path.join(main_dir, "siteconfig.json"))
siteconfig = json.load(open(os.path.join(main_dir, "siteconfig.json"), encoding="utf-8"))

# paths and files
data_dir = to_absolute(siteconfig.get("dataDir", ''))
dicts_path = os.path.join(data_dir, 'dicts')
lexonomy_db_file = os.path.join(data_dir, 'lexonomy.sqlite')
Xref_db_file = os.path.join(data_dir, 'crossref.sqlite')
dbSchemaFile = to_absolute(siteconfig.get("dbSchemaFile", ''))
dbXrefSchemaFile = to_absolute(siteconfig.get("dbXrefSchemaFile", ''))

# ===================================
# UTILS
# ===================================
def get_mainDB_verion(mainDB):
    try:
        r = mainDB.execute("SELECT value FROM configs WHERE id='version'").fetchone()
    except sqlite3.OperationalError:
        # table does not exists
        mainDB.execute("CREATE TABLE IF NOT EXISTS configs (id TEXT PRIMARY KEY, value TEXT)")
        r = {'value': '0.0.0'}

    return r['value']


def get_dict_version(dictDB):
    dict_metadata = {}
    dict_meta = dictDB.execute("SELECT json FROM configs WHERE id='metadata'").fetchone()
    if dict_meta:
        dict_metadata = json.loads(dict_meta['json'])
    dict_version = dict_metadata.get('version', '0.0.0')

    return dict_version, dict_metadata


def get_db(file_path):
    if os.path.isfile(file_path):
        conn = sqlite3.connect(file_path)
        conn.row_factory = sqlite3.Row
        conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on")
        return conn
    else:
        return None


def versiontuple(v):
    return tuple(map(int, (v.split("."))))


def get_key(key, sqlite_row, default=None):
    try:
        return sqlite_row[key]
    except IndexError:
        return default


def get_dict_list():
    dicts = []
    for file in os.listdir(dicts_path):
        if file.endswith('.sqlite'):
            dicts.append(os.path.join(dicts_path, file))

    return dicts


def backup_data():
    destination_dir = os.path.join(data_dir, 'backups', timestamp)

    if not os.path.exists(destination_dir):
        try:
            os.makedirs(destination_dir)
        except OSError:
            print(f'Error: Destination dir ({destination_dir}) for data backup already exists!')
            sys.exit()

    # Backup dicts
    try:
        print(f"Backing up {dicts_path} -> {destination_dir}")
        shutil.copytree(dicts_path, destination_dir, dirs_exist_ok=True)

    except Exception as e:
        print(f"Error during dictionary DB backup! {e}")
        sys.exit()

    # Backup lexonomy DB
    try:
        shutil.copy2(lexonomy_db_file, destination_dir)
        if os.path.isfile(f'{lexonomy_db_file}-shm'):
            shutil.copy2(f'{lexonomy_db_file}-shm', destination_dir)
        if os.path.isfile(f'{lexonomy_db_file}-wal'):
            shutil.copy2(f'{lexonomy_db_file}-wal', destination_dir)
    except Exception as e:
        print(f"Error during lexonomy DB backup!")
        sys.exit()

# ===================================


# ===========================
# INIT NEW DB = new installation
# ===========================
def init_main_db():
    # ============================================
    # MAIN LEXONOMY DATABASE SETUP
    # ============================================
    conn = sqlite3.connect(lexonomy_db_file)

    schema = open(dbSchemaFile, 'r').read()
    try:
        conn.executescript(schema)
        conn.execute('INSERT INTO configs (id, value) VALUES (?,?)', ('version', DBupdates[-1]))
        conn.commit()
        print("Initialized %s with: %s" % (lexonomy_db_file, dbSchemaFile))
    except sqlite3.Error as e:
        print("Problem importing database schema. Likely the DB has already been created. Database error: %s" % e)

    # Add admin users to user database
    if siteconfig.get('admins'):
        for user in siteconfig["admins"]:
            password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
            try:
                conn.execute("insert into users(email, passwordHash) values(?, ?)", (user, passhash))
                conn.commit()
                print("I have created a user account for %s. The password is: %s" % (user, password))
            except sqlite3.Error as e:
                print("Creating a user account for %s has failed. This could be because the account already exists." % user)

    conn.close()

    # ============================================
    # CROSS REFERENCING DATABASE SETUP
    # ============================================
    connXref = sqlite3.connect(Xref_db_file)

    schema = open(dbXrefSchemaFile, 'r').read()
    try:
        connXref.executescript(schema)
        connXref.commit()
        print("Initialized %s with: %s" % (Xref_db_file, dbXrefSchemaFile))
    except sqlite3.Error as e:
        print("Problem importing database schema. Likely the DB has already been created. Database error: %s" % e)

    connXref.close()

# ===========================
# UPDATES
# ===========================
class Updates:
    def update_3_24(self, mainDB):
        # from: 'can_edit', 'can_view', 'can_config', 'can_download', 'can_upload'
        # to: 'canView', 'canEdit', 'canAdd', 'canDelete', 'canEditSource', 'canConfig', 'canDownload', 'canUpload'

        # add new
        for j in ['canView', 'canEdit', 'canAdd', 'canDelete', 'canEditSource', 'canConfig', 'canDownload', 'canUpload']:
            try:
                mainDB.execute(f'ALTER TABLE user_dict ADD COLUMN {j} INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass

        for user_access in mainDB.execute('SELECT * FROM user_dict').fetchall():
            rid = user_access['id']
            # all rights in DB skip
            if get_key('can_view', user_access, None) == None:
                return
            else: # need to modify DB
                # New rights branched out from canEdit
                add = 0
                delete = 0
                edit_source = 0

                # From old
                config_update = get_key('can_config', user_access, 0)
                view = get_key('can_view', user_access, 0)
                edit = get_key('can_edit', user_access, 0)
                download = get_key('can_download', user_access, 0)
                upload = get_key('can_upload', user_access, 0)

                # if user had canEdit right he originally has also add, delete and edit source so keep it
                if edit:
                    add = 1
                    delete = 1
                    edit_source = 1

                # update rights
                mainDB.execute('UPDATE user_dict SET canView=?, canEdit=?, canAdd=?, canDelete=?, canEditSource=?, '
                             'canConfig=?, canDownload=?, canUpload=? WHERE id=?',
                             (view, edit, add, delete, edit_source, config_update, download, upload, rid))

        # remove old
        for i in ['can_edit', 'can_view', 'can_config', 'can_download', 'can_upload']:
            mainDB.execute(f'ALTER TABLE user_dict DROP COLUMN {i}')

        mainDB.commit()

    def update_2_153(self, dictDB):
        #Updates all json entry parts to new format with paths in names -> tag 2.153
        update_payload = []
        update_counter = 0
        for entry in dictDB.execute('SELECT id, nvh FROM entries').fetchall():
            new_json = ops.nvh2jsonDump(entry['nvh'])
            update_payload.append((new_json, entry['id']))
            update_counter += 1

        dictDB.executemany('UPDATE entries SET json=? WHERE id=?', update_payload)

    def update_3_0(self, dictDB):
        # creates only nvh schema and removes json schema from db
        structure_data = json.loads(dictDB.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
        if not structure_data.get('nvhSchema', False) and structure_data.get('elements', False):
            schema_json = structure_data['elements']
            schema_nvh = nvh.schema_json2nvh(schema_json)
            del structure_data['elements']
            structure_data['nvhSchema'] = schema_nvh

            if structure_data.get('tab', False):
                tab = structure_data['tab']
                structure_data['mode'] = 'dmlex' if tab == 'dmlex' else 'custom'
                structure_data['tab'] = 'code' if tab == 'custom' else 'visual'
            else:
                structure_data['mode'] = "custom"
                structure_data['tab'] = "visual"

            dictDB.execute("UPDATE configs SET json=? WHERE id='structure'", (json.dumps(structure_data),))

    def update_3_1(self, dictDB):
        try:
            dictDB.execute("SELECT * FROM entries LIMIT 1").fetchone()['doctype']
            dictDB.execute("ALTER TABLE entries DROP COLUMN doctype")
        except (IndexError, TypeError):
            pass

    def update_3_2(self, dictDB):
        def key2path(key, structure_elements, entry_element):
            for path in structure_elements.keys():
                if path.split('.')[-1] == key:
                    return path
            return f'{entry_element}.{key}'

        def path_format_keys(old_keys):
            for k in old_keys:
                if '.' in k:
                    return True
            return False

        formatting = dictDB.execute("SELECT json FROM configs WHERE id='formatting'").fetchone()
        if formatting:
            formatting_json = json.loads(formatting['json'])
            if not formatting_json.get('elements', False):
                formatting_json = {'elements': formatting_json}

            old_keys = list(formatting_json['elements'].keys())

            if not path_format_keys(old_keys):
                structure_json = json.loads(dictDB.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
                if structure_json.get('nvhSchema', False):
                    structure = structure_json['nvhSchema']
                    entry_element = structure_json['root']
                    structure_elements = nvh.schema_nvh2json(structure)

                    formatting_json['__elements__'] = {}
                    for key in old_keys:
                        new_key = key2path(key, structure_elements, entry_element)
                        formatting_json['__elements__'][new_key] = formatting_json['elements'].pop(key)
                    formatting_json['elements'] = formatting_json['__elements__']
                    formatting_json.pop('__elements__')

                    new_formatting_json = json.dumps(formatting_json)
                    dictDB.execute("UPDATE configs SET json=? WHERE id='formatting'", (new_formatting_json,))
                    dictDB.commit()
                else:
                    raise Exception('schema not in NVH format')

    def update_3_31(self, dictDB):
        if not dictDB.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stats'").fetchone():
            old_entry_count = 0
            old_completed_entries = 0
            old_stats = dictDB.execute("SELECT id, json FROM configs WHERE id IN ('entry_count', 'completed_entries')")
            for item in old_stats.fetchall():
                if item['id'] == 'entry_count':
                    old_entry_count = int(item['json'])
                elif item['id'] == 'completed_entries':
                    old_completed_entries = int(item['json'])

            dictDB.execute("DELETE FROM configs WHERE id='entry_count'")
            dictDB.execute("DELETE FROM configs WHERE id='completed_entries'")
            progress_tracking = {"node": "__lexonomy__complete", "tracked": False}
            dictDB.execute("INSERT INTO configs VALUES (?, ?)", ('progress_tracking', json.dumps(progress_tracking)))

            total_entries = int(dictDB.execute("SELECT COUNT(*) AS total FROM entries").fetchone()['total'])
            if total_entries != old_entry_count:
                sys.stderr.write(f'entry count difference: old: {old_entry_count} new: {total_entries}\n')

            total_competed = int(dictDB.execute("SELECT COUNT(*) AS total FROM entries WHERE nvh LIKE '%__lexonomy__complete:%'").fetchone()['total'])
            if total_competed != old_completed_entries:
                sys.stderr.write(f'entry count difference: old: {old_entry_count} new: {total_entries}\n')

            dictDB.execute("CREATE TABLE stats (id TEXT PRIMARY KEY, value INTEGER)")
            dictDB.execute("INSERT INTO stats VALUES ('entry_count', ?)", (total_entries,))
            dictDB.execute("INSERT INTO stats VALUES ('completed_entries', ?)", (total_competed,))
            dictDB.commit()

    def update_4_0(self, dictDB):
        new_formatting_structure = {"content": {"name": None,
                                                "path": None},
                                    "styles": {},
                                    "children": [],
                                    "orientation": "column"}

        def transform_old_styling(old_node_styling):
            def update_styles(old_key, new_key, value_mapping, styles_subpart, new_node_formatting):
                if old_node_styling[old_key] in [None, 'None']:
                    # skip the None value
                    return

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
                                 4: 24, 5: 32, 6: 40, 
                                 'smaller': 12, 'bigger': 24}
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
                if gutter in ["indent", "hanging"]:
                    if new_node_formatting.get("element"):
                        new_node_formatting["element"]["margin-left"] = 20
                    else:
                        new_node_formatting["element"] = {"margin-left": 20}

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
                new_node_formatting['label']["background-color"] = "#E0E0E0"
                new_node_formatting['label']["padding-top"] = 2
                new_node_formatting['label']["padding-right"] = 5
                new_node_formatting['label']["padding-bottom"] = 2
                new_node_formatting['label']["padding-left"] = 5
                new_node_formatting['label']["margin-right"] = 4
                new_node_formatting['label']["border-radius"] = 5
                new_node_formatting['label']["font-size"] = 14
                new_node_formatting['label']["color"] = "#808080"

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

        # ===================
        # MAIN
        # ===================
        r = dictDB.execute("SELECT json FROM configs WHERE id='formatting'").fetchone()
        if r:
            formatting = json.loads(r['json'])
        else:
            # keep the formatting empty if not present in old dict
            return

        structure = json.loads(dictDB.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
        root = nvh.schema_get_root_name(structure['nvhSchema'])
        hidden_elements = [key for key, value in formatting.get('elements', {}).items() if value.get("hidden", False) == True]
        desktop_layout = get_recur_children(root, nvh.schema_nvh2json(structure['nvhSchema']), formatting, hidden_elements)

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

        if formatting.get('elements'):
            del formatting['elements']
        dictDB.execute("INSERT OR REPLACE INTO configs (id, json) VALUES (?, ?)", ('formatting', json.dumps(formatting)))
        dictDB.commit()


def make_updates(args):
    update_summary = {'dicts_updated': 0, 'dicts_failed': 0, 
                      'mainDB_updated': 0, 'mainDB_failed': 0, 
                      'errors': 0}
    available_updates = Updates()
    mainDB = get_db(lexonomy_db_file)
    is_updated = False

    for update_number in DBupdates:
        for dict_file in get_dict_list():
            new_version = None
            mainDB_version = get_mainDB_verion(mainDB)
            dictDB = get_db(os.path.join(dicts_path, dict_file))
            dict_version, dict_metadata = get_dict_version(dictDB)

            try:
                if update_number in dictDB_updates: 
                    if versiontuple(dict_version) < versiontuple(update_number):
                        new_version = update_number
                        method_name = 'update_' + re.sub('\.', '_', update_number)
                        method_to_call = getattr(available_updates, method_name)
                        method_to_call(dictDB)
                        print(f'OK dict ({dict_version}->{new_version}): {dict_file}')
                        update_summary['dicts_updated'] += 1
                elif update_number in mainDB_updates:
                    if versiontuple(mainDB_version) < versiontuple(update_number):
                        new_version = update_number
                        method_name = 'update_' + re.sub('\.', '_', update_number)
                        method_to_call = getattr(available_updates, method_name)
                        method_to_call(mainDB)
                        print(f'OK main DB ({mainDB_version}->{new_version}): lexonomy.sqlite')
                        update_summary['mainDB_updated'] += 1
                    else:
                        # New version for dict
                        if versiontuple(dict_version) < versiontuple(update_number):
                            new_version = update_number
                else:
                    print(f'ERROR: declaration of update_{update_number} not available!')
                    update_summary['errors'] += 1

                if new_version:
                    is_updated = True
                    # Update versions
                    if versiontuple(dict_version) < versiontuple(update_number):
                        dict_metadata['version'] = new_version
                        dictDB.execute('INSERT OR REPLACE INTO configs (id, json) VALUES (?,?)', ('metadata', json.dumps(dict_metadata)))
                        dictDB.commit()
                    if versiontuple(mainDB_version) < versiontuple(update_number):
                        mainDB.execute('INSERT OR REPLACE INTO configs (id, value) VALUES (?,?)', ('version', new_version))
                        mainDB.commit()
            except Exception as e:
                if update_number in mainDB_updates:
                    print(f'\033[31mFAIL main DB ({mainDB_version}->{new_version}) {type(e).__name__}: {e}|{dict_file}\033[0m')
                    update_summary['mainDB_failed'] += 1
                elif update_number in dictDB_updates:
                    print(f'\033[31mFAIL dict ({dict_version}->{new_version}) {type(e).__name__}: {e}|{dict_file}\033[0m')
                    update_summary['dicts_failed'] += 1

                if args.debug:
                    import traceback
                    traceback.print_exc()

            dictDB.close()

    mainDB.close()

    print('=========================')
    print('SUMMARY:')
    for key, value in update_summary.items():
        print('  ' + key.replace("_", " ") + ': ' + str(value))
    print('=========================')

    if is_updated:
        print('Update completed.')
    else:
        print('No updates done, everything seems to be up to date.')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Script for initialization/updating lexonomy databases during install and deploy')
    parser.add_argument('--debug', action='store_true', required=False, default=False,
                        help='Print traceback for debugging')
    parser.add_argument('--no-backup', action='store_true', required=False, default=False,
                        help="Don't backup the data.")
    args = parser.parse_args()

    print('Using files:')
    print(f'\tsiteconfig: {os.path.join(main_dir, "siteconfig.json")}')
    print(f'\tlexonomy_db_file: "{lexonomy_db_file}"')
    print(f'\tXref_db_file: "{Xref_db_file}"')
    print(f'\tdicts_path: "{dicts_path}"')
    print(f'\tdbSchemaFile: "{dbSchemaFile}"')
    print(f'\tdbXrefSchemaFile: "{dbXrefSchemaFile}"')

    os.makedirs(data_dir, exist_ok=True)
    os.chmod(data_dir, stat.S_IRWXU | stat.S_IRWXG)
    os.makedirs(dicts_path, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'sqlite_tmp'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'projects'), exist_ok=True)

    if not os.path.isfile(lexonomy_db_file) and not os.path.isfile(Xref_db_file):
        print(f'Initializing new Lexonomy DB file: {lexonomy_db_file}')
        init_main_db()
    else:
        print(f'Updating Lexonomy.')
        if not args.no_backup:
            backup_data()
        make_updates(args)


if __name__ == '__main__':
    main()
