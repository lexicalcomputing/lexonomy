#!/usr/bin/python3.10

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops
import import2dict
import sqlite3

current_dir = os.path.dirname(os.path.realpath(__file__))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import (rewrite) configs of a dictionary')
    parser.add_argument('config', type=str,
                        help='Dictionary configs in JSON format')
    parser.add_argument('dict_id', type=str,
                        help='Dictionary ID')

    args = parser.parse_args()

    config_json = None
    if args.config:
        with open(args.config) as f:
            config_json = json.load(f)

    siteconfig = json.load(open(os.path.join(current_dir, "..", "siteconfig.json"), encoding="utf-8"))

    if not os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts/" + args.dict_id) + ".sqlite"):
        sys.stderr.write(f'ERROR: DictID {args.dict_id} does not exist\n')
        sys.exit()

    db = sqlite3.connect(f'{siteconfig["dataDir"]}/dicts/{args.dict_id}.sqlite')
    db.row_factory = sqlite3.Row

    import2dict.import_configs(db, args.dict_id, config_json)

    db.close()

if __name__ == '__main__':
    main()
