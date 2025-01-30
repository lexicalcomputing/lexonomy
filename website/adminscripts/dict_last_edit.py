#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json
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
    parser.add_argument('-p', '--dicts-path', type=str,
                        required=True,
                        help='Path to directory with all lexonomy dictionaries')
    parser.add_argument('-d', '--db_path', type=str,
                        required=True,
                        help='Lexonomy main db.')
    args = parser.parse_args()

    total_dicts = 0

    dict_last_edit = {}
    for root, dirs, files in os.walk(args.dicts_path):
        for file_name in files:
            total_dicts += 1 
            try:
                dict_id = file_name[:-7]
                db = get_db(os.path.join(root, file_name))
                res_c = db.execute("SELECT MAX([when]) as date FROM history;")
                date_str = res_c.fetchone()['date'][:7]
                date_format = '%Y-%m'
                date_obj = datetime.strptime(date_str, date_format)
                dict_last_edit[dict_id] = date_obj
                db.close()
            except:
                continue

    result_csv = []
    for k, v in reverse_dict(dict_last_edit).items():
        result_csv.append((k.strftime("%Y-%m"), len(v), v))
    result_csv = sorted(result_csv, key=lambda x: x[0])

    with open('lexonomy_last_edit.csv', 'w') as f:
        f.write('last_access\tno_of_dicts\tdicts\n')
        for i in result_csv:
            f.write(f'{i[0]}\t{i[1]}\t{i[2]}\n')

    # Making plot
    left = [x[0] for x in result_csv]
    height = [x[1] for x in result_csv]
    plt.figure(figsize=(30,10))
    plt.bar(left, height, tick_label = left,
        width = 0.8, color = ['blue'])
    addlabels(left, height)
    plt.xticks(rotation=90, ha='right')
    plt.xlabel('Date')
    plt.ylabel('Edited dicts no.')
    plt.title(f'Processed {len(dict_last_edit.keys())} out of {total_dicts} ({total_dicts - len(dict_last_edit.keys())} skipped)')
    plt.tight_layout()
    plt.savefig('lexonomy_last_edit.png')
    
if __name__ == '__main__':
    main()
