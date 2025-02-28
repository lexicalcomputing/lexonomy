#!/usr/bin/python3.10
# coding: utf-8
# Author: Tomas Svoboda, tomas.svoboda@sketchengine.eu, Lexical Computing CZ
import os
import re
import sys
import json
import traceback


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


def migrate_to_3_0(config, titling_element='', entry_element='', structure_elements=[]):
    if 'ident' in config:
        config['ident']['direction'] = 'ltr'

    if 'xemplate' in config:
        _rename_keys(config, [('xemplate', 'formatting')])
        if config['formatting'].get('_css'):
            _rename_keys(config['formatting'], [('_css', 'customCss')])
            config['formatting']['useCustomCss'] = True

        for key, value in config['formatting'].items():
            if key not in ['_xsl', 'customCss', 'useCustomCss']:
                if 'shown' not in value or not value['shown']:
                    value['hidden'] = True

                _delete_keys(value, ['shown'])

    if 'editing' in config:
        _delete_keys(config['editing'], ['xonomyMode', 'xonomyTextEditor'])
        _rename_keys(config['editing'], [('_js', 'js'), ('_css', 'css'), ('_useOwnEditor', 'useOwnEditor')])

    if 'subbing' in config:
        del config['subbing']

    config['ske'] = {}
    if 'kex' in config:
        for key in ['corpus', 'concquery', 'concsampling', 'searchElements']:
            if key in config['kex']:
                config['ske'][key] = config['kex'][key]
    for source, dest in [
        ('xampl', 'exampleContainer'),
        ('thes', 'thesaurusContainer'),
        ('defo', 'definitionContainer'),
        ('collx', 'collocationContainer')
    ]:
        if source in config and 'container' in config[source]:
            config['ske'][dest] = config[source]['container']
    _delete_keys(config, ['kex', 'xampl', 'thes', 'defo', 'collx', 'xema', 'users'])

    # Setting defaults
    if titling_element:
        config['titling']['headword'] = titling_element
        config['titling']['headwordSorting'] = titling_element

    if entry_element and config['formatting'].get(entry_element, False):
        config['formatting'][entry_element]['hidden'] = False

    # converting to paths
    if structure_elements:
        def key2path(key):
            for path in structure_elements.keys():
                if path.split('.')[-1] == key:
                    return path
            return f'{entry_element}.{key}'

        if config.get('formatting', False):
            old_keys = list(config['formatting'].keys())
            config['formatting']['__elements__'] = {}
            for key in old_keys:
                if key not in ['_xsl', 'customCss', 'useCustomCss']:
                    new_key = key2path(key)
                    config['formatting']['__elements__'][new_key] = config['formatting'].pop(key)
            config['formatting']['elements'] = config['formatting']['__elements__']
            config['formatting'].pop('__elements__')

        if config.get('titling', False):
            for i in ['headword', 'headwordSorting']:
                if config['titling'].get(i, False):
                    config['titling'][i] = key2path(config['titling'][i])
            if config['titling'].get('headwordAnnotations', False):
                new_list = []
                for i in config['titling']['headwordAnnotations']:
                    new_list.append(key2path(i))
                config['titling']['headwordAnnotations'] = new_list
            if config['titling'].get('headwordAnnotationsAdvanced', False):
                new_key = config['titling']['headwordAnnotationsAdvanced']
                for key in re.findall(r'%\(([^\)]+)\)', config['titling']['headwordAnnotationsAdvanced']):
                    new_key = re.sub('%\('+key+'\)', '%('+key2path(key)+')', new_key)
                config['titling']['headwordAnnotationsAdvanced'] = new_key

        if config.get('searchability', False) and config['searchability'].get('searchableElements', False):
            new_list = []
            for i in config['searchability']['searchableElements']:
                new_list.append(key2path(i))
            config['searchability']['searchableElements'] = new_list

        if config.get('flagging', False) and config['flagging'].get('flag_element', False):
            config['flagging']['flag_element'] = key2path(config['flagging']['flag_element'])

        if config.get('ske', False):
            if config['ske'].get('searchElements', False):
                new_list = []
                for i in config['ske']['searchElements']:
                    new_list.append(key2path(i))
                config['ske']['searchElements'] = new_list

            for i in ['collocationContainer', 'exampleContainer', 'collocationContainer', 'definitionContainer', 'thesaurusContainer']:
                if config['ske'].get(i, False):
                    config['ske'][i] = key2path(config['ske'][i])
            if config['ske'].get('concquery'):
                new_key = config['ske']['concquery']
                for key in re.findall(r'%\(([^\)]+)\)', config['ske']['concquery']):
                    new_key = re.sub('%\('+key+'\)', '%('+key2path(key)+')', new_key)
                config['ske']['concquery'] = new_key


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
    try:
        with open(args.config_path) as f:
            config = json.load(f)
            migrated_config = migrate_config(config, '3.0')
        output_path = args.out if args.out else args.config_path
        with open(output_path, 'w') as f:
            f.writelines(json.dumps(migrated_config))
    except Exception as e:
        sys.stderr.write(f'Error {args.config_path}: {e}\n{traceback.format_exc()}\n')


if __name__ == '__main__':
    main()
