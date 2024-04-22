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

# currdir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
siteconfig_file_path = os.environ.get("LEXONOMY_SITECONFIG", os.path.join(main_dir, "siteconfig.json"))
siteconfig = json.load(open(siteconfig_file_path, encoding="utf-8"))
path = os.path.join(siteconfig["dataDir"], 'lexonomy.sqlite')
pathXref = os.path.join(siteconfig["dataDir"], 'crossref.sqlite')


def init_dbs():
    # ============================================
    # MAIN LEXONOMY DATABASE SETUP
    # ============================================
    conn = sqlite3.connect(path)
    print("Connected to database: %s" % path)

    if siteconfig.get("dbSchemaFile", False):
        schema = open(siteconfig["dbSchemaFile"], 'r').read()
        try:
            conn.executescript(schema)
            conn.commit()
            print("Initialized %s with: %s" % (path, siteconfig["dbSchemaFile"]))
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
    connXref = sqlite3.connect(pathXref)
    print("Connected to database: %s" % pathXref)

    if siteconfig.get("dbXrefSchemaFile", False):
        schema = open(siteconfig["dbXrefSchemaFile"], 'r').read()
        try:
            connXref.executescript(schema)
            connXref.commit()
            print("Initialized %s with: %s" % (pathXref, siteconfig["dbXrefSchemaFile"]))
        except sqlite3.Error as e:
            print("Problem importing database schema. Likely the DB has already been created. Database error: %s" % e)
    else:
        print("Unknown database schema, please add dbXrefSchemaFile to siteconfig.json")

    connXref.close()


def update_dbs():
    print("Updating lexonomy database: %s" % path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    #### HELPER FUNCTIONS ####

    def get_table_column_names(conn, table):
        r = conn.execute("PRAGMA table_info(%s)" % table)
        return set([x[1] for x in r.fetchall()])

    def do_query(conn, q):
        try:
            conn.execute(q)
        except sqlite3.Error as e:
            print("Database error: %s" % e)
            print("Query was: '%s'" % q)

    #### ADDING NEW TABLES ####

    do_query(conn, "CREATE TABLE IF NOT EXISTS recovery_tokens (email text, requestAddress text, token text, expiration datetime, usedDate datetime, usedAddress text)")
    do_query(conn, "CREATE TABLE IF NOT EXISTS register_tokens (email text, requestAddress text, token text, expiration datetime, usedDate datetime, usedAddress text)")
    do_query(conn, "CREATE TABLE IF NOT EXISTS dict_fav (dict_id text, user_email text)")
    do_query(conn, "CREATE INDEX IF NOT EXISTS fav_dict_id on dict_fav (dict_id)")
    do_query(conn, "CREATE INDEX IF NOT EXISTS fav_user_email on dict_fav (user_email)")

    #### ADDING COLUMNS TO EXISTING TABLES ####

    upgrades = {
        "users": [("ske_id", "INTEGER"), ("ske_username", "TEXT"), ("consent", "INTEGER"), ("ske_apiKey", "TEXT"), ("comment", "TEXT"), 
                  ("annotator_role", "JSON"), ("created_by", "TEXT"), ("is_manager", "INTEGER")],
        "dicts": [("language", "TEXT"), ("public", "BOOLEAN DEFAULT false"), ("configs", "JSON")],
        "user_dict": [("can_config", "INTEGER"), ("can_download", "INTEGER"), ("can_upload", "INTEGER"), ("can_view", "INTEGER"), 
                      ("can_edit", "INTEGER")]
    }

    for db, newcols in upgrades.items():
        db_columns = get_table_column_names(conn, db)
        for column in newcols:
            if column[0] not in db_columns:
                do_query(conn, "ALTER TABLE %s ADD COLUMN %s %s" % (db, column[0], column[1]))

    #### COMMIT & DONE ####
    conn.commit()
    conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Script to initialize database and users, from the siteconfig.json file')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    args = parser.parse_args()

    if not os.path.isfile(path) and not os.path.isfile(pathXref):
        init_dbs()
    else:
        update_dbs()


if __name__ == '__main__':
    main()
