#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict


def get_db(filename):
    conn = sqlite3.connect(filename)
    conn.row_factory = sqlite3.Row
    conn.executescript("PRAGMA journal_mode=WAL;")
    conn.commit()
    return conn


def reverse_dict(data: dict) -> dict:
    rd = defaultdict(list)
    for k, v in data.items():
        rd[v].append(k)
    return rd


def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i], y[i], ha = 'center')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Examine last access to dictionary')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-p', '--dicts-path', type=str,
                        required=True,
                        help='Path to directory with all lexonomy dictionaries')
    args = parser.parse_args()

    dict_size = {}

    for line in args.input:
        dict_id = line.strip()
        # Dict size
        if not dict_size.get(dict_id, False):
            db = get_db(os.path.join(args.dicts_path, dict_id+'.sqlite'))
            res_total = db.execute("SELECT COUNT(*) AS total FROM entries")
            total_entries = res_total.fetchone()['total']
            dict_size[dict_id] = int(total_entries)

    result_csv = {'0-100': 0, '100-1000': 0, '>1000': 0}
    for size, dict_list in reverse_dict(dict_size).items():
        if size <= 100:
            result_csv['0-100'] += len(dict_list)
        elif size > 100 and size <= 1000:
            result_csv['100-1000'] += len(dict_list)
        if size > 100:
            result_csv['>1000'] += len(dict_list)

    args.output.write('dict_id\tsize\tlast_access\tcategory\n')
    for did, size in dict_size.items():
        cat = 'None'
        if size <= 100:
            cat = '0-100'
        elif size > 100 and size <= 1000:
            cat = '100-1000'
        if size > 100:
            cat = '>1000'
        args.output.write(f'{did}\t{size}\t{cat}\n')

if __name__ == '__main__':
    main()
