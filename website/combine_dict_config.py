#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json

def merge2json(json_file, js_file, css_file, structure_file, tl_node):
    config = {}

    if json_file and os.path.isfile(json_file):
        with open(json_file, 'r') as f:
            config = json.load(f)

    js_data = ''
    if js_file and os.path.isfile(js_file):
        with open(js_file, 'r') as fj:
            js_data = fj.read()

    css_data = ''
    if css_file and os.path.isfile(css_file):
        with open(css_file, 'r') as fc:
            css_data = fc.read()

    if js_data or css_data:
        if config.get('editing'):
            config['editing']['useOwnEditor'] = True
            config['editing']['js'] = js_data,
            config['editing']['css'] = css_data
        else:
            config['editing'] = {'useOwnEditor': True,
                                'js': js_data,
                                'css': css_data}

    if structure_file and os.path.isfile(structure_file):
        with open(structure_file, 'r') as f:
            if config.get('structure'):
                config['structure']["root"] = tl_node
                config['structure']["nvhSchema"] = f.read()
            else:
                config['structure'] = {"root": tl_node,
                                       "nvhSchema": f.read()}
    return config


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Combine parts of config into one object/file')
    parser.add_argument('tl_node', type=str,
                        help='Top level NVH node')
    parser.add_argument('config_parts', type=str, nargs='*',
                        help='Config parts')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    args = parser.parse_args()

    ordered_extensions = ['.json', '.css', '.js', '.nvh']

    files = {}
    for file in args.config_parts:
        for ext in ordered_extensions:
            if file.endswith(ext) and ext not in files:
                files[ext] = file
                break
    config = merge2json(files.get('.json'), files.get('.js'), files.get('.css'), files.get('.nvh'), args.tl_node)
    args.output.write(json.dumps(config, indent=4))


if __name__ == '__main__':
    main()