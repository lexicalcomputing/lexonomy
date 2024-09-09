#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import sys
from pprint import pprint

node_line_re = re.compile('^([^\s:]+):\s*([^\s]*)\s*"(.*)"\s*$')
children_line_re = re.compile('^\s+(.*)@(.*):\s*(.*)\s*$')

def print_recur_children(n, nodes, modules, out, indent=2):
    n_name = n[0]
    n_num = n[1]

    # NODE
    if n_num:
        out.append(f'{" "*indent}{n_name}:')
    else:
        out.append(f'{" "*indent}{n_name}: {n_num}')

    # PROPERTIES
    if nodes[n_name]['values']:
        out.append(f' {nodes[n_name]["values"]}')
    if nodes[n_name]['required']:
        out.append(' ~.+')
    out.append('\n')

    # CHILDREN
    for module, mod_ch in nodes[n_name]['children'].items():
        if module in modules:
            for ch in mod_ch:
                print_recur_children(ch, nodes, modules, out, indent+2)


def get_dmlex_schema(input_lines, start_node, modules):
    # ====================
    # Parsing all modules form txt file
    # ====================
    out = []
    nodes = {}
    desc_dict = {}
    for line in input_lines:
        if line.startswith('#') or line.strip() == '':
            continue
        
        node_line = node_line_re.match(line)
        children_line = children_line_re.match(line)

        if node_line:
            node_name = node_line.group(1)
            node_values = node_line.group(2)
            node_description = node_line.group(3)

            nodes[node_name] = {"required": node_values=="!", 
                                "values": node_values if node_values!='!' else "",
                                "description": node_description,
                                "children": {}}
            desc_dict[node_name] = node_description
            # print(f'N: NAME: "{node_name}", VAL: "{node_values}", DESC: "{node_description}"')
        elif children_line:
            child_module = children_line.group(1)
            child_name = children_line.group(2)
            child_number = children_line.group(3)

            if nodes[node_name]["children"].get(child_module, False):
                nodes[node_name]["children"][child_module].append((child_name, child_number))
            else:
                nodes[node_name]["children"][child_module] = [(child_name, child_number)]

    out.append(f'{start_node}:\n')
    for module, mod_ch in nodes[start_node]['children'].items():
        if module in modules:
            for ch in mod_ch:
                print_recur_children(ch, nodes, modules, out)

    return out, desc_dict


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-s', '--start_node', type=str,
                        required=False, default="entry",
                        help='The top level node')
    parser.add_argument('-d', '--print_descriptions', action='store_true',
                        required=False, default=False,
                        help='Print with description')
    parser.add_argument('-m', '--modules', type=str,
                        required=False, default="core",
                        help='Comma separated list of modules to include. Available: [core|xlingual|values|linking|etymology|annotation]')
    args = parser.parse_args()

    out, desc_dict = get_dmlex_schema(args.input, args.start_node, args.modules)

    for l in out:
        args.output.write(l)
    
    if args.print_descriptions:
        for key, value in desc_dict.items():
            args.output.write(f'{key}: {value}\n')


if __name__ == '__main__':
    main()