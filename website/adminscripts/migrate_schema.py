#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json
import sqlite3
from nvh import nvh

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db(filename):
    conn = sqlite3.connect(filename)
    conn.row_factory = sqlite3.Row
    conn.executescript("PRAGMA journal_mode=WAL;")
    conn.commit()
    return conn


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-d', '--db_path', type=str,
                        required=True,
                        help='Path to sqlite DB')
    args = parser.parse_args()

    db = get_db(args.db_path)
    r = db.execute('SELECT json FROM configs WHERE id="structure"')
    c = r.fetchone()
    structure_json =  json.loads(c['json'])
    try:
        nvh_schema = nvh.parse_string(structure_json['custom_NVHSchema'])
        elements = {}
        nvh_schema.build_json(elements)
        structure_json['elements'] = elements

        db.execute('UPDATE configs SET json=? WHERE id="structure"', (json.dumps(structure_json),))
        db.commit()
    except Exception as e:
        sys.stderr.write(f'Error migrating {args.db_path}\n')
    db.close()
    
if __name__ == '__main__':
    main()
