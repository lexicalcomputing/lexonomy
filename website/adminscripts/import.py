#!/usr/bin/python3

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops
import import2dict

current_dir = os.path.dirname(os.path.realpath(__file__))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import NVH/XML to dictionary with init and config')
    parser.add_argument('filename', type=str,
                        help='import file name')
    parser.add_argument('email', type=str,
                        default='IMPORT@LEXONOMY', help='user email')
    parser.add_argument('main_node_name', type=str,
                        help='Name of the mani node of the entry (headword, entry, ...)')
    parser.add_argument('title', type=str,
                        help='Dictionary title')
    parser.add_argument('dict_id', type=str,
                        help='Dictionary ID')
    parser.add_argument('lang', type=str,
                        help='language')
    parser.add_argument('--config', type=str,
                        required=False, default='',
                        help='Dictionary config in JSON format')
    parser.add_argument('-p', '--purge', action='store_true',
                        required=False, default=False,
                        help='Backup and purge dictionary history')
    parser.add_argument('-pp', '--purge_all', action='store_true',
                        required=False, default=False,
                        help='Purge dictionary with history and all configs without backup')
    parser.add_argument('-d', '--deduplicate', action='store_true',
                        required=False, default=False,
                        help='Deduplicate nodes with same name and value on the same level')
    parser.add_argument('-c', '--clean', action='store_true',
                        required=False, default=False,
                        help='Renaming node names that appear under different parents')

    args = parser.parse_args()

    config_json = None
    if args.config:
        with open(args.config) as f:
            config_json = json.load(f)

    siteconfig = json.load(open(os.path.join(current_dir, "..", "siteconfig.json"), encoding="utf-8"))

    if os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts/" + args.dict_id) + ".sqlite"):
        sys.stderr.write(f'ERROR: DictID {args.dict_id} already exists\n')
        sys.exit()

    dictDB = ops.initDict(args.dict_id, args.title, args.lang, "", args.email)
    dict_config = {"limits": {"entries": 10000000000}}
    ops.registerDict(dictDB, args.dict_id, args.email, dict_config)
    ops.attachDict(args.dict_id, {})
    dictDB.close()
    import2dict.import_data(f'{siteconfig["dataDir"]}/dicts/{args.dict_id}.sqlite', args.filename, args.email, args.main_node_name, 
                            args.purge, args.purge_all, args.deduplicate, args.clean, config_data=config_json)

    print(args.dict_id)
if __name__ == '__main__':
    main()