#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import re
import sys
from collections import OrderedDict

xlingual_prefixed = frozenset(['explanation', 'translation', 'exampleTranslation'])
linking_prefixed = ('relation', 'member')
etymology_prefixed = frozenset(['etymonUnit'])

node_line_re = re.compile('^([^\s:]+):\s*([^\s]*)\s*"(.*)"\s*$')
children_line_re = re.compile('^\s+(.*)@(.*):\s*(.*)\s*$')

def get_recur_children(n, result, nodes, acc_mod, modules, node2prefixes, linking_member_names, indent=2):
    n_name = n[0]
    n_num = n[1]

    if nodes.get(n_name, False):
        node_source_info = nodes[n_name]
    else:
        node_source_info = nodes['\\S*' + n_name.split('_', 1)[1]]
    # NODE
    result[n_name] = {"children": {}, 'indent': indent, 'num': n_num, 'values': node_source_info["values"], 're': '~.+' if node_source_info['required'] else '', 'module': acc_mod}

    # CHILDREN
    for mod, mod_ch in node_source_info['children'].items():
        if mod in modules or 'all' in modules:
            for ch in mod_ch:
                ch_name = ch[0]
                ch_num = ch[1]
                if node2prefixes.get(ch_name[3:], False):
                    for x in node2prefixes[ch_name[3:]]:
                        get_recur_children((f'{x}_{ch_name[3:]}', ch_num), result[n_name]["children"], nodes, mod, modules, node2prefixes, [], indent+2)
                elif ch_name[3:] == linking_prefixed[1]: # linking module
                    if len(linking_member_names) == 1: # if one member requires at least two
                        get_recur_children((f'{linking_member_names[0]}_{ch_name[3:]}', ch_num), result[n_name]["children"], nodes, mod, modules, node2prefixes, [], indent+2)
                    else:
                        for m in linking_member_names: # if two memebers require at least one
                            get_recur_children((f'{m}_{ch_name[3:]}', '+'), result[n_name]["children"], nodes, mod, modules, node2prefixes, [], indent+2)
                else:
                    get_recur_children(ch, result[n_name]["children"], nodes, mod, modules, node2prefixes, [], indent+2)


def get_dmlex_schema(input_lines, start_node, modules, xlingual_langs, linking_relations, etymology_langs):
    # ====================
    # Parsing all modules form txt file
    # ====================
    result = OrderedDict()
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

    node2prefixes = {}
    if xlingual_langs:
        for l in xlingual_prefixed:
            node2prefixes[l] = xlingual_langs
    if etymology_langs:
        for el in etymology_prefixed:
            node2prefixes[el] = etymology_langs
    # ====================
    # Building schema
    # ====================
    result[start_node] = {"children": {}, 'indent': 0, 'num': "", 'values': '', 're': '', 'module': 'core'}
    for mod, mod_ch in nodes[start_node]['children'].items():
        if mod in modules or 'all' in modules:
            for ch in mod_ch:
                ch_name = ch[0]
                ch_num = ch[1]
                if node2prefixes.get(ch_name[3:], False):
                    for x in node2prefixes[ch_name[3:]]:
                        get_recur_children((f'{x}_{ch_name[3:]}', ch_num), result[start_node]["children"], nodes, mod, modules, node2prefixes, [])
                elif ch_name[3:] == linking_prefixed[0]: # linking module
                    for key, value in linking_relations.items():
                        get_recur_children((f'{key}_{ch_name[3:]}', ch_num), result[start_node]["children"], nodes, mod, modules, node2prefixes, value)
                else:
                    get_recur_children(ch, result[start_node]["children"], nodes, mod, modules, node2prefixes, [])

    return result, desc_dict


def final_schema2str(data, schema, used_modules):
    for key, value in data.items():
        used_modules.add(value['module'])
        node_line = ''
        node_line += " "*value["indent"] + key + ":"
        if value["num"]:
            node_line += f' {value["num"]}'
        if value["values"]:
            node_line += f' {value["values"]}'
        if value["re"]:
            node_line += f' {value["re"]}'

        schema.append(node_line + '\n')

        final_schema2str(value["children"], schema, used_modules)


def main():
    # cat dictTemplates/dmlex_modules.txt | ./dmlex2schema.py -s "lexicographicResource" -m "all" -l "en,fr,de" -r "meronymy:part:whole;synonymy:syn" -e "een,efr"
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
                        help='The top level node. Tested for "entry" and "lexicographicResource"')
    parser.add_argument('-d', '--print_descriptions', action='store_true',
                        required=False, default=False,
                        help='Print with description.')
    parser.add_argument('-m', '--modules', type=str,
                        required=False, default="core",
                        help='Comma separated list of modules to include. Available: '
                             '[core|xlingual|values|linking|etymology|annotation]')
    parser.add_argument('-l', '--xlingual_langs', type=str,
                        required=False, default=None,
                        help='List of langs. String comma separated.')
    parser.add_argument('-r', '--linking_relations', type=str,
                        required=False, default=None,
                        help='Dict with relations names and their members. String format "relation1:member1:member2;relation2:member21:member22".')
    parser.add_argument('-e', '--etymology_langs', type=str,
                        required=False, default=None,
                        help='Lis of langs for etymology. String comma separated.')
    args = parser.parse_args()

    # =============================================
    # assigning relations members under the relation
    # =============================================
    linking_relations = {}
    if args.xlingual_langs:
        for relation in args.linking_relations.strip().split(';'):
            rel_name = relation.strip().split(':')[0]
            rel_members = relation.strip().split(':')[1:]
            linking_relations[rel_name] = rel_members
    # =============================================

    result, desc_dict = get_dmlex_schema(args.input, args.start_node, args.modules,
                                         args.xlingual_langs.strip().split(',') if args.xlingual_langs else [],
                                         linking_relations,
                                         args.etymology_langs.strip().split(',') if args.etymology_langs else [])

    schema = []
    used_modules = set()
    final_schema2str(result, schema, used_modules)
    args.output.write(''.join(schema))
    
    if args.print_descriptions:
        for key, value in desc_dict.items():
            args.output.write(f'{key}: {value}\n')
        args.output.write(f'Used modules: {", ".join(used_modules)}\n')


if __name__ == '__main__':
    main()