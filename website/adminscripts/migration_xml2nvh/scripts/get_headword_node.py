#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import sys
import json
import sqlite3

def main():
    import argparse
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-d', '--data_path', type=str,
                        required=True,
                        help='Path to data folder')

    parser.add_argument('-f', '--fix', type=str,
                        required=False, default=None,
                        help='Path to csv with fixes')

    args = parser.parse_args()

    fixes = {}
    if args.fix:
        with open(args.fix, 'r') as f:
            for line in f:
                dictID, hw_node = line.strip().split('\t')
                fixes[dictID] = hw_node

    for dbname in args.input:
        dbname = dbname.strip()
        db = sqlite3.connect(f'{args.data_path}/{dbname}.sqlite')
        db.row_factory = sqlite3.Row
        try:
            c0 = db.execute('SELECT json FROM configs WHERE id="titling"')
            r0 = c0.fetchone()
            if r0:
                titling_json = json.loads(r0['json'])
                haeadword_node = titling_json.get('headword', '')
                locale = titling_json.get('locale', 'en_FALLBACK')
                if haeadword_node.strip() == '':
                    haeadword_node = 'headword'
                if fixes.get(dbname, False):
                    args.output.write(f'{dbname}.xml\t{dbname}\t{fixes[dbname]}\t{locale}\tFIX\n')
                else:
                    args.output.write(f'{dbname}.xml\t{dbname}\t{haeadword_node}\t{locale}\t-\n')
            else:
                if fixes.get(dbname, False):
                    args.output.write(f'{dbname}.xml\t{dbname}\t{fixes[dbname]}\t{locale}\tFIX\n')
                else:
                    args.output.write(f'{dbname}.xml\t{dbname}\theadword\ten_FALLBACK\tFALLBACK\n')

        except sqlite3.OperationalError:
            sys.stderr.write(f'No configs for {dbname}\n')

if __name__ == '__main__':
    main()
