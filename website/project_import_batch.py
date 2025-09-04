#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import ops
import sys
import json
from import2dict import import_data
from log_subprocess import log_err
from combine_dict_config import merge2json


currdir = os.path.dirname(os.path.abspath(__file__))
siteconfig = json.load(open(os.path.join(currdir, "siteconfig.json"), encoding="utf-8"))

def update_project_info(batch_size, user, nvh_file_path, project_id, stage, tl_node, time_stamp):
    # =======================================
    dict_id = ops.suggestDictId()

    main_db = ops.getMainDB()
    main_db.execute("INSERT INTO project_dicts (project_id, dict_id, source_nvh, stage, status, created) VALUES (?,?,?,?,?,?)",
                    (project_id, dict_id, nvh_file_path, stage, 'creating', time_stamp))
    main_db.commit()

    file_name = nvh_file_path.rsplit('/', 1)[1]
    batch_name = ' '.join(file_name.rstrip('.in').split('.'))

    c = main_db.execute('SELECT * FROM projects WHERE id=?', (project_id,))
    r = c.fetchone()
    language = r['language']

    dictDB = ops.initDict(dict_id, batch_name, language, "", user)
    dict_config = {"limits": {"entries": int(batch_size)}}
    ops.registerDict(dictDB, dict_id, user, dict_config)
    ops.attachDict(dict_id, {})

    dbpath = os.path.join(siteconfig["dataDir"], "dicts/"+dict_id+".sqlite")

    # =======================================
    # Create config from project config files
    # =======================================
    project_path = os.path.join(siteconfig["dataDir"], "projects", project_id)

    config = merge2json(os.path.join(project_path, stage+'_batch.json'),
                        os.path.join(project_path, stage+'_batch.js'),
                        os.path.join(project_path, stage+'_batch.css'),
                        os.path.join(project_path, stage+'_batch.nvh'),
                        tl_node)
    # =======================================

    import_data(dbpath, nvh_file_path, project_id, tl_node, config_data=config)

    main_db.execute("UPDATE project_dicts SET status=? WHERE project_id=? AND dict_id=?", ('inProgress', project_id, dict_id))
    main_db.commit()
    main_db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Import one batch to project')
    parser.add_argument('user', type=str, help='User email')
    parser.add_argument('tl_node', type=str, help='Top Level NVH Node')
    parser.add_argument('ts', type=str, help='Time stamp')
    parser.add_argument('-i', '--file_path', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    args = parser.parse_args()

    file_path = args.file_path.readline().strip()

    if file_path:
        project_id = file_path.split('/')[-3]
        stage = file_path.split('/')[-2]
        batch_size = 0
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip().startswith(f'{args.tl_node}:'):
                    batch_size += 1

        update_project_info(batch_size, args.user, file_path, project_id, stage, args.tl_node, args.ts)
    else:
        log_err('EMPTY INPUT')


if __name__ == '__main__':
    main()
