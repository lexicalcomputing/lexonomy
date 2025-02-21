#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import sys
import json
import sqlite3


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Dump public dicts')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-d', '--dicts', type=str,
                        required=True,
                        help='Path to dicts sqlite files')

    args = parser.parse_args()
    import os

    for root, dirs, files in os.walk(args.dicts):
        for file_name in files:
            if file_name.endswith('.sqlite'):
                db = sqlite3.connect(os.path.join(root, file_name))
                db.row_factory = sqlite3.Row
                try:
                    q = db.execute("SELECT json FROM configs WHERE id='publico'")
                    r = json.loads(q.fetchone()['json'])
                    if r.get('public', False) and r['public'] == True:
                        args.output.write(f'{file_name[:-7]}\n')
                except:
                    pass
                db.close()


if __name__ == '__main__':
    main()
