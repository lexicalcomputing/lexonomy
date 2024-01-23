#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import sqlite3

sys.path.append('../')
from ops import nvh2json

current_dir = os.path.dirname(os.path.realpath(__file__))


def getDB(dictID):
    if os.path.isfile(dictID):
        conn = sqlite3.connect(dictID)
        conn.row_factory = sqlite3.Row
        # WAL (Write-Ahead Logging): In this mode, changes are not written directly to the database file. Instead, a separate WAL file is used to store the changes.
        # forein keys: maintain referential integrity between the tables, meaning that relationships between tables are consistent and valid
        conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on")
        return conn
    else:
        return None


def makeDict(example_dir, sqlite_schema, output_db):
    
    sql_schema = open(sqlite_schema, 'r').read()
    conn = sqlite3.connect(output_db)
    conn.executescript(sql_schema)
    conn.commit()
    #update dictionary info
    dictDB = getDB(output_db)

    for file in os.listdir(f'{example_dir}'):
        if file.endswith('.nvh'):
            with open(os.path.join(example_dir, file), 'r') as f:
                nvh = f.read()
                idx = file[:-4].split('_')[1]
                dictDB.execute("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (idx, 'entry', nvh, nvh2json(nvh), '<span class="headword">' + file[:-4] + '</span>', file[:-4], 0, 0, 0))

    dictDB.commit()
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create testing DB from example NVH files')
    parser.add_argument('-d', '--example_dir', type=str,
                        required=True,
                        help='Directory with NVH examples.')
    parser.add_argument('-s', '--sqlite_schema', type=str,
                        required=True,
                        help='SQLite schema file.')
    parser.add_argument('-o', '--output_db', type=str,
                        required=True,
                        help='SQLite schema file.')
    args = parser.parse_args()
    makeDict(args.example_dir, args.sqlite_schema, args.output_db)

if __name__ == '__main__':
    main()