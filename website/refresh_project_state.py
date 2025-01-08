#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ

import os
import ops
import json
import project
import fileinput
from nvh import nvh

currdir = os.path.dirname(os.path.abspath(__file__))
siteconfig = json.load(open(os.path.join(currdir, "siteconfig.json"), encoding="utf-8"))


def refresh_selected_stages(project_id, all_stages):
    if all_stages:
        project_info = project.getProject(project_id)
        for stage in all_stages:
            # batches shouldn't be generated form more than one source
            dict_id = None
            query = None
            for s in project_info['workflow']:
                if s['stage'] == stage:
                    dict_id = s['inputDicts'][0]['dictID']
                    query = s['query']
            if dict_id and query:
                refresh_project_remaining(project_id, dict_id, stage, query, project_info['tl_node'])


def refresh_project_remaining(projectID, dict_id, stage, query, tl_node='entry'):
    ###################
    # dict values
    ###################
    conn = ops.getMainDB()
    c1 = conn.execute("SELECT source_nvh, status, remaining "
                      "FROM project_dicts "
                      "WHERE dict_id=? AND project_id=?", (dict_id, projectID))
    r1 = c1.fetchone()
    source_nvh = r1['source_nvh']

    ###################
    # NVH source entries
    ###################
    infile = fileinput.input([source_nvh], encoding="utf8")
    dictionary = nvh.parse_file(infile)
    dictionary = dictionary.filter_entries(query.split(","), [], 0)

    source_entries = set()
    for c in dictionary.children:
        source_entries.add(c.value)

    remaining_entries = len(source_entries)
    ###################
    # exported entries
    ###################
    stage_dir = os.path.join(siteconfig["dataDir"], 'projects', projectID , stage)
    if os.path.isdir(stage_dir):
        for file in os.listdir(stage_dir):
            if file.endswith('.in'):
                with open(os.path.join(stage_dir, file), 'r', encoding="utf8") as fd:
                    for line in fd:
                        if line.startswith(f'{tl_node}:'):
                            if line[len(tl_node)+1:].strip() in source_entries:
                                remaining_entries -= 1
    ###################
    # update remaining
    ###################
    source_remaining = json.loads(r1['remaining'])
    source_remaining[stage] = remaining_entries

    conn.execute('UPDATE project_dicts SET remaining=? WHERE dict_id=? AND project_id=?',
                 (json.dumps(source_remaining), dict_id, projectID))
    conn.commit()
    conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Refresh remaining headwords in project stage dict')
    parser.add_argument('project_id', type=str, help='Project ID')
    parser.add_argument('dict_id', type=str, help='Stage')
    args = parser.parse_args()

    ###################
    # Stages that uses dict as source
    ###################
    project_info = project.getProject(args.project_id)
    dependent_stages = set()
    for s in project_info['workflow']:
        for d in s['inputDicts']:
            if d['dictID'] == args.dict_id:
                dependent_stages.add((s['stage'], s.get('query', '')))

    ###################
    for stage, query in dependent_stages:
        if query:
            refresh_project_remaining(args.project_id, args.dict_id, stage, query, project_info['tl_node'])

if __name__ == '__main__':
    main()
