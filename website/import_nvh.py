#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import ops
import sys
import json
import sqlite3
import datetime
import fileinput
from nvh import nvh


def purge(db, historiography, args):
    if args.purge_all:
        print("Purging history...")
        db.execute("delete from history")
    else:
        print("Copying all entries to history...")
        db.execute("insert into history(entry_id, action, [when], email, xml, historiography) "
                   "select id, 'purge', ?, ?, xml, ? from entries", 
                   (str(datetime.datetime.utcnow()), args.email, json.dumps(historiography)))
        
    print("Purging entries...")
    db.execute("delete from entries")
    db.execute("delete from linkables")
    db.execute("delete from searchables")
    db.commit()

    print("Compressing database...")
    db.execute("vacuum")
    db.commit()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import entries from NVH into Lexonomy SQLite database')
    parser.add_argument('dbname', type=str, 
                        help='database file name')
    parser.add_argument('filename', type=str, 
                        help='import file name')
    parser.add_argument('email', type=str,
                        default='IMPORT@LEXONOMY', help='user email')
    parser.add_argument('main_node_name', type=str,
                        help='Name of the mani node of the entry (headword, entry, ...)')
    parser.add_argument('-p', '--purge', action='store_true',
                        required=False, default=False,
                        help='backup and purge dictionary history')
    parser.add_argument('-pp', '--purge_all', action='store_true',
                        required=False, default=False,
                        help='purge dictionary history without backup')
    args = parser.parse_args()

    print("PID "+ str(os.getpid()) + '\n')
    print("Import started. You may close the window, "
          "import will run in the background. Please wait...\n")


    import_nvh, pase_err = nvh.parse_file(fileinput.input(args.filename))
    import_entries, tl_name = import_nvh.get_entries()
    entry_count = len(import_entries)

    # print(tl_name)
    # print([x.dump_string() for x in import_entries])
    # print(entry_count)

    entry_inserted = 0
    limit_reached = False
    max_import = 1000

    # dictID = os.path.basename(args.dbname).replace(".sqlite", "")
    db = sqlite3.connect(args.dbname)
    db.row_factory = sqlite3.Row
    historiography={"importStart": str(datetime.datetime.utcnow()), "filename": os.path.basename(args.filename)}

    if args.purge:
        purge(db, historiography, args)

    configs = ops.readDictConfigs(db)
    dict_stats = ops.getDictStats(db)
    limit = configs["limits"]["entries"] if configs.get("limits") and configs["limits"].get("entries") else 5000
    max_import = limit - dict_stats["entryCount"]
    if max_import < entry_count:
        print("Detected %d entries in '%s' element, only %d will be imported" % (entry_count, tl_name, max_import))
    else:
        print("Detected %d entries in '%s' element" % (entry_count, tl_name))

    needs_refac = 0
    needs_resave = 1 if configs["searchability"].get("searchableElements") and len(configs["searchability"].get("searchableElements")) > 0 else 0


    for entry in import_entries:
        entry_str = entry.dump_string()
        if entry_inserted >= max_import:
            limit_reached = True
            break
        action = "create"
        entry_key = ops.getEntryHeadword(entry, args.main_node_name)
        title = "<span class='headword'>" + entry_key + "</span>"
        c = db.execute("SELECT id FROM entries WHERE sortkey=?", (entry_key,))
        if not c.fetchone():
            sql = "insert into entries(nvh, json, needs_refac, needs_resave, needs_refresh, doctype, title, sortkey) values(?, ?, ?, ?, ?, ?, ?, ?)"
            params = (entry_str, ops.nvh2json(entry_str), needs_refac, needs_resave, 0, tl_name, title, entry_key)
        else:
            sql = "insert into entries(nvh, json, needs_refac, needs_resave, needs_refresh, doctype, title, sortkey) values(?, ?, ?, ?, ?, ?, ?, ?)"
            params = (entry_str, ops.nvh2json(entry_str), needs_refac, needs_resave, 0, tl_name, title, entry_key)
            action = "update"
        c = db.execute(sql, params)
        entryID = c.lastrowid
        db.execute("insert into history(entry_id, action, [when], email, nvh, historiography) values(?, ?, ?, ?, ?, ?)", 
                   (entryID, action, str(datetime.datetime.utcnow()), args.email, entry_str, json.dumps(historiography)))
        db.execute("delete from searchables where entry_id=? and level=?", (entryID, 1))
        searchTitle = ops.getEntryTitle(entry, configs["titling"], True)
        db.execute("insert into searchables(entry_id, txt, level) values(?, ?, ?)", (entryID, searchTitle, 1))
        db.execute("insert into searchables(entry_id, txt, level) values(?, ?, ?)", (entryID, searchTitle.lower(), 1))
        entry_inserted += 1

        if entry_inserted % 100 == 0:
            print("\r%.2d%% (%d/%d entries imported)" % ((entry_inserted/entry_count*100), entry_inserted, entry_count), end='')

    print("\r%.2d%% (%d/%d entries imported)" % ((entry_inserted/entry_count*100), entry_inserted, entry_count))

    if limit_reached:
        print("\r100%% (%d/%d entries imported). Entry limit was reached. To remove the limit, " \
              "email inquiries@sketchengine.eu and give details of your dictionary project." % (entry_inserted, entry_count))

    db.commit()


if __name__ == '__main__':
    main()
