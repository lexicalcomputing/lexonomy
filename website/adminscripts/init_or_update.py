#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json
import random
import string
import sqlite3
import hashlib

sys.path.insert(0, os.path.split(os.path.dirname(os.path.abspath(sys.argv[0])))[0])
import ops

main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
siteconfig_file_path = os.path.join(main_dir, "siteconfig.json")
siteconfig = json.load(open(siteconfig_file_path, encoding="utf-8"))
lexonomy_db_file = os.path.join(siteconfig["dataDir"], 'lexonomy.sqlite')
Xref_db_file = os.path.join(siteconfig["dataDir"], 'crossref.sqlite')
dicts_path = os.path.join(siteconfig["dataDir"], 'dicts')


def init_main_db():
    # ============================================
    # MAIN LEXONOMY DATABASE SETUP
    # ============================================
    conn = sqlite3.connect(lexonomy_db_file)
    print("Connected to database: %s" % lexonomy_db_file)

    if siteconfig.get("dbSchemaFile", False):
        schema = open(siteconfig["dbSchemaFile"], 'r').read()
        try:
            conn.executescript(schema)
            conn.execute('INSERT INTO configs (id, value) VALUES (?,?)', ('version', ops.get_version()))
            conn.commit()
            print("Initialized %s with: %s" % (lexonomy_db_file, siteconfig["dbSchemaFile"]))
        except sqlite3.Error as e:
            print("Problem importing database schema. Likely the DB has already been created. Database error: %s" % e)
    else:
        print("Unknown database schema, please add dbSchemaFile to siteconfig.json")

    # Add admin users to user database
    if siteconfig.get('admins', False):
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
    print("Connected to database: %s" % Xref_db_file)

    if siteconfig.get("dbXrefSchemaFile", False):
        schema = open(siteconfig["dbXrefSchemaFile"], 'r').read()
        try:
            connXref.executescript(schema)
            connXref.commit()
            print("Initialized %s with: %s" % (Xref_db_file, siteconfig["dbXrefSchemaFile"]))
        except sqlite3.Error as e:
            print("Problem importing database schema. Likely the DB has already been created. Database error: %s" % e)
    else:
        print("Unknown database schema, please add dbXrefSchemaFile to siteconfig.json")

    connXref.close()


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


def update_main_db():
    def access_rights_3_24(conn):
        # from: 'can_edit', 'can_view', 'can_config', 'can_download', 'can_upload'
        # to: 'canView', 'canEdit', 'canAdd', 'canDelete', 'canEditSource', 'canConfig', 'canDownload', 'canUpload'

        # add new
        for j in ['canView', 'canEdit', 'canAdd', 'canDelete', 'canEditSource', 'canConfig', 'canDownload', 'canUpload']:
            try:
                conn.execute(f'ALTER TABLE user_dict ADD COLUMN {j} INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass

        for user_access in conn.execute('SELECT * FROM user_dict').fetchall():
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
                conn.execute('UPDATE user_dict SET canView=?, canEdit=?, canAdd=?, canDelete=?, canEditSource=?, '
                             'canConfig=?, canDownload=?, canUpload=? WHERE id=?',
                             (view, edit, add, delete, edit_source, config_update, download, upload, rid))

        # remove old
        for i in ['can_edit', 'can_view', 'can_config', 'can_download', 'can_upload']:
            conn.execute(f'ALTER TABLE user_dict DROP COLUMN {i}')

        conn.commit()

    # ==========================================
    # main
    # ==========================================
    print("Updating main db ...")
    conn = get_db(os.path.join(dicts_path, lexonomy_db_file))

    try:
        r = conn.execute("SELECT value FROM configs WHERE id='version'").fetchone()
    except sqlite3.OperationalError:
        # table does not exists
        conn.execute("CREATE TABLE IF NOT EXISTS configs (id TEXT PRIMARY KEY, value TEXT)")
        r = {'value': '0.0.0'}

    version = r['value']
    new_version = None
    # ========================
    # UPDATES
    # ========================
    try:
        if versiontuple(version) < versiontuple('3.24'):
            new_version = '3.24'
            access_rights_3_24(conn)
            print(f'OK ({new_version})')

        if new_version:
            # Update version
            conn.execute('INSERT OR REPLACE INTO configs (id, value) VALUES (?,?)', ('version', new_version))
            conn.commit()
    except Exception as e:
        print(f'ERROR ({new_version}) {type(e).__name__}: {e}')

    conn.close()


def update_dict_db():
    #Updates all json entry parts to new format with paths in names -> tag 2.153
    def update_json_2_153(conn):
        update_payload = []
        update_counter = 0
        for entry in conn.execute('SELECT id, nvh FROM entries').fetchall():
            new_json = ops.nvh2jsonDump(entry['nvh'])
            update_payload.append((new_json, entry['id']))
            update_counter += 1

        conn.executemany('UPDATE entries SET json=? WHERE id=?', update_payload)

    # creates only nvh schema and removes json schema from db
    def update_schema_3_0(conn):
        from nvh import nvh
        structure_data = json.loads(conn.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
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

            conn.execute("UPDATE configs SET json=? WHERE id='structure'", (json.dumps(structure_data),))

    def rm_doctype_3_1(conn):
        try:
            conn.execute("SELECT * FROM entries LIMIT 1").fetchone()['doctype']
            conn.execute("ALTER TABLE entries DROP COLUMN doctype")
        except (IndexError, TypeError):
            pass

    def formatting_path_keys_3_2(conn):
        from nvh import nvh
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

        formatting = conn.execute("SELECT json FROM configs WHERE id='formatting'").fetchone()
        if formatting:
            formatting_json = json.loads(formatting['json'])
            if not formatting_json.get('elements', False):
                formatting_json = {'elements': formatting_json}

            old_keys = list(formatting_json['elements'].keys())

            if not path_format_keys(old_keys):
                structure_json = json.loads(conn.execute("SELECT json FROM configs WHERE id='structure'").fetchone()['json'])
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
                    conn.execute("UPDATE configs SET json=? WHERE id='formatting'", (new_formatting_json,))
                    conn.commit()
                else:
                    raise Exception('schema not in NVH format')

    def dict_stats_3_3(conn):
        if not conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stats'").fetchone():
            old_entry_count = 0
            old_completed_entries = 0
            old_stats = conn.execute("SELECT id, json FROM configs WHERE id IN ('entry_count', 'completed_entries')")
            for item in old_stats.fetchall():
                if item['id'] == 'entry_count':
                    old_entry_count = int(item['json'])
                elif item['id'] == 'completed_entries':
                    old_completed_entries = int(item['json'])

            conn.execute("DELETE FROM configs WHERE id='entry_count'")
            conn.execute("DELETE FROM configs WHERE id='completed_entries'")
            progress_tracking = {"node": "__lexonomy__completed", "tracked": False}
            conn.execute("INSERT INTO configs VALUES (?, ?)", ('progress_tracking', json.dumps(progress_tracking)))

            total_entries = int(conn.execute("SELECT COUNT(*) AS total FROM entries").fetchone()['total'])
            if total_entries != old_entry_count:
                sys.stderr.write(f'entry count difference: old: {old_entry_count} new: {total_entries}\n')

            total_competed = int(conn.execute("SELECT COUNT(*) AS total FROM entries WHERE nvh LIKE '%__lexonomy__completed:%'").fetchone()['total'])
            if total_competed != old_completed_entries:
                sys.stderr.write(f'entry count difference: old: {old_entry_count} new: {total_entries}\n')

            conn.execute("CREATE TABLE stats (id TEXT PRIMARY KEY, value INTEGER)")
            conn.execute("INSERT INTO stats VALUES ('entry_count', ?)", (total_entries,))
            conn.execute("INSERT INTO stats VALUES ('completed_entries', ?)", (total_competed,))
            conn.commit()

    # ===========================================
    # main
    # ===========================================
    print("Updating dicts ...")
    for file in os.listdir(dicts_path):
        if file.endswith('.sqlite'):
            conn = get_db(os.path.join(dicts_path, file))

            metadata = {}
            dict_meta = conn.execute("SELECT json FROM configs WHERE id='metadata'").fetchone()
            if dict_meta:
                metadata = json.loads(dict_meta['json'])
            version = metadata.get('version', '0.0.0')
            new_version = None
            # ========================
            # UPDATES
            # ========================
            try:
                if versiontuple(version) < versiontuple('2.153'):
                    new_version = '2.153'
                    update_json_2_153(conn)
                    print(f'OK ({new_version}): {file}')

                if versiontuple(version) < versiontuple('3.0'):
                    new_version = '3.0'
                    update_schema_3_0(conn)
                    print(f'OK ({new_version}): {file}')

                if versiontuple(version) < versiontuple('3.1'):
                    new_version = '3.1'
                    rm_doctype_3_1(conn)
                    print(f'OK ({new_version}): {file}')

                if versiontuple(version) < versiontuple('3.2'):
                    new_version = '3.2'
                    formatting_path_keys_3_2(conn)
                    print(f'OK ({new_version}): {file}')

                if versiontuple(version) < versiontuple('3.3'):
                    new_version = '3.3'
                    dict_stats_3_3(conn)
                    print(f'OK ({new_version}): {file}')

                if new_version:
                    # Update version
                    metadata['version'] = new_version
                    conn.execute('INSERT OR REPLACE INTO configs (id, json) VALUES (?,?)', ('metadata', json.dumps(metadata)))
                    conn.commit()
            except Exception as e:
                print(f'ERROR ({new_version}) {type(e).__name__}: {e}|{file}')

            conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Script for initialization/updating lexonomy databases during install and deploy')
    parser.parse_args()

    if not os.path.isfile(lexonomy_db_file) and not os.path.isfile(Xref_db_file):
        init_main_db()
    else:
        update_main_db()
        update_dict_db()


if __name__ == '__main__':
    main()
