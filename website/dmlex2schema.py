#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import sys

node_line_re = re.compile('^([^\s:]+):\s*([^\s]*)\s*"(.*)"\s*$')
children_line_re = re.compile('^\s+(.*)@(.*):\s*(.*)\s*$')

def get_recur_children(n, result, nodes, modules, indent=2):
    n_name = n[0]
    n_num = n[1]

    node_source_info = nodes[n_name]
    # NODE
    result[n_name] = {"children": {}, 'indent': indent, 'num': n_num, 'values': node_source_info["values"], 're': '~.+' if node_source_info['required'] else ''}

    # CHILDREN
    for module, mod_ch in node_source_info['children'].items():
        if module in modules:
            for ch in mod_ch:
                get_recur_children(ch, result[n_name]["children"], nodes, modules, indent+2)


def get_dmlex_schema(input_lines, start_node, modules):
    # ====================
    # Parsing all modules form txt file
    # ====================
    result = {}
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
        elif children_line:
            child_module = children_line.group(1)
            child_name = children_line.group(2)
            child_number = children_line.group(3)

            if nodes[node_name]["children"].get(child_module, False):
                nodes[node_name]["children"][child_module].append((child_name, child_number))
            else:
                nodes[node_name]["children"][child_module] = [(child_name, child_number)]

    result[start_node] = {"children": {}, 'indent': 0, 'num': "", 'values': '', 're': ''}
    for module, mod_ch in nodes[start_node]['children'].items():
        if module in modules:
            for ch in mod_ch:
                get_recur_children(ch, result[start_node]["children"], nodes, modules)

    final_schema = []
    final_schema2str(result, final_schema)

    return final_schema, desc_dict


def final_schema2str(data, out):
    for key, value in data.items():
        node_line = ''
        node_line += " "*value["indent"] + key + ":"
        if value["num"]:
            node_line += f' {value["num"]}'
        if value["values"]:
            node_line += f' {value["values"]}'
        if value["re"]:
            node_line += f' {value["re"]}'

        out.append(node_line + '\n')

        final_schema2str(value["children"], out)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate DMLex schema according to selected module and and languages.')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=False, default=sys.stdout,
                        help='Output')
    parser.add_argument('-s', '--start_node', type=str,
                        required=False, default="entry",
                        help='The top level node.')
    parser.add_argument('-d', '--print_descriptions', action='store_true',
                        required=False, default=False,
                        help='Print with description.')
    parser.add_argument('-m', '--modules', type=str,
                        required=False, default="core",
                        help='Comma separated list of modules to include. Available: [core|xlingual|values|linking|etymology|annotation]')
    args = parser.parse_args()

    final_schema, desc_dict = get_dmlex_schema(args.input, args.start_node, args.modules)

    args.output.write(''.join(final_schema))
    
    if args.print_descriptions:
        for key, value in desc_dict.items():
            args.output.write(f'{key}: {value}\n')


if __name__ == '__main__':
    main()