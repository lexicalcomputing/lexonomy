#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ

import os
import sys
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import ops
import import2dict
import fileinput
from nvh import nvh
from migrate_config import migrate_to_3_0
from import2dict import get_gen_schema_elements

current_dir = os.path.dirname(os.path.realpath(__file__))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import NVH/XML to dictionary with init and config')
    parser.add_argument('data_folder', type=str,
                        help='Folder with XML or JSON dump')
    parser.add_argument('config_folder', type=str,
                        help='Folder to dictionary JSON config')
    parser.add_argument('lexonomy_dicts_folder', type=str,
                        help='lexonomy dicts folder')
    parser.add_argument('-c', '--user_credentials', type=str, required=False, default=None,
                        help='Users credentials')

    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    args = parser.parse_args()

    for line in args.input:
        _, dict_id, titling_element, locale, note = line.strip().split('\t')
        title = dict_id
        lang = locale[:2]

        # ===========================
        # Transform XML to NVH
        # ===========================
        sys.stderr.write(f'XML2NVH {args.data_folder}/{dict_id}.xml -> {args.data_folder}/{dict_id}.xml.xml2nvh.nvh\n')
        with open(f'{args.data_folder}/{dict_id}.xml.xml2nvh.nvh', 'w') as f:
            entry_element = import2dict.xml2nvh(f'{args.data_folder}/{dict_id}.xml', f, titling_element)

        # ===========================
        # JSON dict configuration
        # ===========================
        with open(f'{args.config_folder}/{dict_id}.json.orig') as f:
            config_json = json.load(f)
            users = config_json["users"].copy()
            import_nvh = nvh.parse_file(fileinput.input(f'{args.data_folder}/{dict_id}.xml.xml2nvh.nvh'))
            schema = {}
            import_nvh.generate_schema(schema, tln=True)
            structure_elements = {}
            get_gen_schema_elements(schema, structure_elements)

            migrate_to_3_0(config_json, titling_element, entry_element, structure_elements)
            with open(f'{args.config_folder}/{dict_id}.json', 'w') as f_out:
                json.dump(config_json, f_out, indent = 4)

        if os.path.isfile(f"{args.lexonomy_dicts_folder}/{dict_id}.sqlite"):
            sys.stderr.write(f'ERROR: DictID {dict_id} already exists\n')
            sys.exit()

        dictDB = ops.initDict(dict_id, title, lang, "", "old@lexonomy.eu")
        dict_config = {"limits": {"entries": 10000000000}}
        ops.attachDict(dictDB, dict_id, users, dict_config)
        dictDB.close()

        if args.user_credentials:
            credentials = {}
            with open(args.user_credentials, 'r') as csvfile:
                data = csv.reader(csvfile, delimiter=',')
                for row in data:
                    credentials[row[0]] = {'passwordHash': row[1],
                                           'apiKey': row[4],
                                           'ske_id': row[5],
                                           'ske_username': row[6],
                                           'ske_apiKey': row[8]}
            mainDB = ops.getMainDB()
            for user_mail in users:
                if credentials.get(user_mail, False):
                    mainDB.execute("INSERT OR IGNORE INTO users (email,passwordHash,apiKey,ske_id,ske_username,ske_apiKey,created_by) VALUES (?,?,?,?,?,?,?)", 
                                   (user_mail, credentials[user_mail]['passwordHash'], credentials[user_mail]['apiKey'], credentials[user_mail]['ske_id'],
                                    credentials[user_mail]['ske_username'], credentials[user_mail]['ske_apiKey'], 'old@lexonomy.eu'))
            mainDB.commit()
            mainDB.close()

        import2dict.import_data(f'{args.lexonomy_dicts_folder}/{dict_id}.sqlite', f'{args.data_folder}/{dict_id}.xml.xml2nvh.nvh',
                                   email="old@lexonomy.eu", entry_element=entry_element, titling_element=titling_element, config_data=config_json)

if __name__ == '__main__':
    main()
