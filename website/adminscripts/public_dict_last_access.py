#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

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
    args = parser.parse_args()

    public_dicts = set()
    total_dicts = 0
    with open(args.pubdict_list, 'r') as f:
        for line in f:
            total_dicts += 1
            public_dicts.add(line.strip())

    dict_last_access = {}

    for line in args.input:
        if len(line.strip().split(' ')) == 3:
            _, dict_id, date_str = line.strip().rsplit(' ')
            date_str = date_str[:7]
            if dict_id in public_dicts:
                date_format = '%Y-%m'
                date_obj = datetime.strptime(date_str, date_format)
                if dict_last_access.get(dict_id, False):
                    if dict_last_access[dict_id] < date_obj:
                        dict_last_access[dict_id] = date_obj
                else:
                    dict_last_access[dict_id] = date_obj

    result_csv = []
    for k, v in reverse_dict(dict_last_access).items():
        result_csv.append((k.strftime("%Y-%m"), len(v), v))
    result_csv = sorted(result_csv, key=lambda x: x[0])

    with open('lexonomy_public_last_access.csv', 'w') as f:
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
    plt.ylabel('Public dicts access no.')
    plt.title(f'Processed {len(dict_last_access.keys())} out of {total_dicts} ({total_dicts - len(dict_last_access.keys())} skipped)')
    plt.tight_layout()
    plt.savefig('lexonomy_public_last_access.png')
    
if __name__ == '__main__':
    main()
