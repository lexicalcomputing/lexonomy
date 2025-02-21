#!/usr/bin/python3.10
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
siteconfig_file_path = os.environ.get("LEXONOMY_SITECONFIG", os.path.join(main_dir, "siteconfig.json"))
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


def update_main_db():
    # ========================
    # UPDATING MAIN LEXONOMY DB
    # ========================
    def get_table_column_names(conn, table):
        r = conn.execute("PRAGMA table_info(%s)" % table)
        return set([x[1] for x in r.fetchall()])

    def do_query(conn, q):
        try:
            conn.execute(q)
        except sqlite3.Error as e:
            print("Database error: %s" % e)
            print("Query was: '%s'" % q)

    print("Updating lexonomy database: %s" % lexonomy_db_file)
    upgrades = {}
    if upgrades:
        conn = get_db(lexonomy_db_file)

        for db, newcols in upgrades.items():
            db_columns = get_table_column_names(conn, db)
            for column in newcols:
                if column[0] not in db_columns:
                    do_query(conn, "ALTER TABLE %s ADD COLUMN %s %s" % (db, column[0], column[1]))

        conn.commit()
        conn.close()


def update_dict_db():
    def versiontuple(v):
        return tuple(map(int, (v.split("."))))

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
        conn.execute("ALTER TABLE entries DROP COLUMN doctype")

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

                if new_version:
                    # Update version
                    metadata['version'] = new_version
                    conn.execute('INSERT OR REPLACE INTO configs (id, json) VALUES (?,?)', ('metadata', json.dumps(metadata)))
                    conn.commit()
                else:
                    print(f'Already updated: {file}')
            except Exception as e:
                print(f'ERROR ({new_version}) {e}: {file}')

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
