#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt


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
    parser.add_argument('-d', '--pubdict-list', type=str,
                        required=True,
                        help='List of public dicts ids')
    parser.add_argument('-p', '--dicts-path', type=str,
                        required=True,
                        help='Path to directory with all lexonomy dictionaries')
    args = parser.parse_args()

    public_dicts = set()
    total_dicts = 0
    with open(args.pubdict_list, 'r') as f:
        for line in f:
            total_dicts += 1
            public_dicts.add(line.strip())

    dict_last_access = {}
    dict_size = {}

    for line in args.input:
        if len(line.strip().split(' ')) == 3:
            _, dict_id, date_str = line.strip().rsplit(' ')
            date_str = date_str[:7]
            if dict_id in public_dicts:
                # Dict size
                if not dict_size.get(dict_id, False):
                    db = get_db(os.path.join(args.dicts_path, dict_id+'.sqlite'))
                    res_total = db.execute("SELECT COUNT(*) AS total FROM entries")
                    total_entries = res_total.fetchone()['total']
                    dict_size[dict_id] = int(total_entries)

                # Dict last access
                date_format = '%Y-%m'
                date_obj = datetime.strptime(date_str, date_format)
                if dict_last_access.get(dict_id, False):
                    if dict_last_access[dict_id] < date_obj:
                        dict_last_access[dict_id] = date_obj
                else:
                    dict_last_access[dict_id] = date_obj

    result_csv = {'0-100': 0, '100-1000': 0, '>1000': 0}
    for size, dict_list in reverse_dict(dict_size).items():
        if size <= 100:
            result_csv['0-100'] += len(dict_list)
        elif size > 100 and size <= 1000:
            result_csv['100-1000'] += len(dict_list)
        if size > 100:
            result_csv['>1000'] += len(dict_list)

    with open('lexonomy_public_dict_sizes.csv', 'w') as f:
        f.write('dict_id\tsize\tlast_access\tcategory\n')
        for did, size in dict_size.items():
            if dict_last_access.get(did, False):
                last_acc = dict_last_access[did].strftime("%Y-%m")
            else:
                last_acc = 'None'
            cat = 'None'
            if size <= 100:
                cat = '0-100'
            elif size > 100 and size <= 1000:
                cat = '100-1000'
            if size > 100:
                cat = '>1000'
            f.write(f'{did}\t{size}\t{last_acc}\t{cat}\n')

    # Making plot
    left = list(result_csv.keys())
    height = [result_csv[i] for i in left]
    plt.figure(figsize=(30,10))
    plt.bar(left, height, tick_label = left,
        width = 0.8, color = ['blue'])
    addlabels(left, height)
    plt.xlabel('Entry count')
    plt.ylabel('No. of public dicts')
    plt.title(f'Total no. of dicts: {total_dicts}')
    plt.tight_layout()
    plt.savefig('lexonomy_public_dict_sizes.png')

if __name__ == '__main__':
    main()
