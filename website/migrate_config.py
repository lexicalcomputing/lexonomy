#!/usr/bin/python3.10
# coding: utf-8
# Author: Tomas Svoboda, tomas.svoboda@sketchengine.eu, Lexical Computing CZ
import os
import json


def _delete_keys(dictionary, keys):
    for key in keys:
        if key in dictionary:
            del dictionary[key]


def _rename_keys(dictionary, keys):
    for keyTuple in keys:
        old_key = keyTuple[0]
        new_key = keyTuple[1]
        if old_key in dictionary:
            dictionary[new_key] = dictionary.pop(old_key)


def migrate_to_3_0(config):
    if 'ident' in config:
        config['ident']['direction'] = 'ltr'

    if 'users' in config:
        for user_config in config['users'].values():
            user_config['canView'] = True

    if 'xemplate' in config:
        _rename_keys(config, [('xemplate', 'formatting')])
        for key, value in config['formatting'].items():
            if 'shown' not in value or not value['shown']:
                value['hidden'] = True
            _delete_keys(value, ['shown'])

    if 'editing' in config:
        _delete_keys(config['editing'], ['xonomyMode', 'xonomyTextEditor'])
        _rename_keys(config['editing'], [('_js', 'js'), ('_css', 'css'), ('_useOwnEditor', 'useOwnEditor')])

    if 'subbing' in config:
        del config['subbing']

    return config


def migrate_config(config, version):
    old_version = config.get("version", None)
    if not old_version:
        config = migrate_to_3_0(config)
    config['version'] = version
    return config


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert dictionary configuration to the latest version.')
    parser.add_argument('config_path', type=str,
                        help='Path to dictionary config.json file')
    parser.add_argument('-o', '--out',
                        required=False, default='',
                        help='Result output path. If not specified, input file is overwritten.')
    args = parser.parse_args()
    with open(args.config_path) as f:
        config = json.load(f)
        migrated_config = migrate_config(config, '3.0')
    output_path = args.out if args.out else args.config_path
    with open(output_path, 'w') as f:
        f.writelines(json.dumps(migrated_config))


if __name__ == '__main__':
    main()
