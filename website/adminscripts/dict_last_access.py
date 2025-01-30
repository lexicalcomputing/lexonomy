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

    check_access_for_users = {}
    total_dicts = 0

    for root, dirs, files in os.walk(args.dicts_path):
        for file_name in files:
            total_dicts += 1 
            try:
                db = get_db(os.path.join(root, file_name))
                #sys.stderr.write(f'Reading: {os.path.join(root, file_name)}\n')
                res_c = db.execute("SELECT json FROM configs WHERE id='users'")
                config = json.loads(res_c.fetchone()['json'])
                for mail, rights in config.items():
                    if rights.get('canEdit', False) == True:
                        if check_access_for_users.get(mail):
                            check_access_for_users[mail].append(file_name[:-7])
                        else:
                            check_access_for_users[mail] = [file_name[:-7]]
                db.close()
            except:
                #sys.stderr.write(f'Skipping: {os.path.join(root, file_name)}\n')
                continue

    dict_last_access = {}
    lexonomy_db = get_db(args.db_path)
    res_t = lexonomy_db.execute("SELECT email, sessionLast FROM users WHERE email IN ('" + "','".join(check_access_for_users.keys()) + "')")
    for i in res_t.fetchall():
        if i['sessionLast'] and i['sessionLast'].strip() != '':
            date_str = str(i['sessionLast'])[:7]
            date_format = '%Y-%m'
            date_obj = datetime.strptime(date_str, date_format)

            for dict_id in check_access_for_users[i['email']]:
                if dict_last_access.get(dict_id, False):
                    if dict_last_access[dict_id] < date_obj:
                        dict_last_access[dict_id] = date_obj
                else:
                    dict_last_access[dict_id] = date_obj

    lexonomy_db.close()

    result_csv = []
    for k, v in reverse_dict(dict_last_access).items():
        result_csv.append((k.strftime("%Y-%m"), len(v), v))
    result_csv = sorted(result_csv, key=lambda x: x[0])

    with open('lexonomy_last_access.csv', 'w') as f:
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
    plt.ylabel('Accessed dicts no.')
    plt.title(f'Processed {len(dict_last_access.keys())} out of {total_dicts} ({total_dicts - len(dict_last_access.keys())} skipped)')
    plt.tight_layout()
    plt.savefig('lexonomy_last_access.png')
    
if __name__ == '__main__':
    main()
