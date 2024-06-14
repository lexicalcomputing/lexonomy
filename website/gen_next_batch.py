#!/usr/bin/python3.10
# coding: utf-8
# usage: gen_next_batch.py BATCH_SIZE [MAX_BATCHES] [EXISTING_BATCHES_FILEMASK] [USER_EMAIL]
import os
import sys
import glob
import ops
import json
import subprocess
from log_subprocess import log_err, log_info, log_warning, log_end, log_start

currdir = os.path.dirname(os.path.abspath(__file__))
siteconfig = json.load(open(os.path.join(currdir, "siteconfig.json"), encoding="utf-8"))


def get_already_exported(batch_list, tl_name):
    already_exported = set()
    for filename in batch_list:
        for line in open(filename):
            if line.startswith(tl_name + ': '):
                already_exported.add(line.strip('\n').split(': ', 1)[1])
    return already_exported


def split_to_batches(input, max_batches, batch_size , batch_list, tl_node, already_exported, batch_dir, stage):
    remaining_hws = 0
    hw_idx = -1
    batches_generated = 0
    curr_batch = None
    next_batch_num = len(batch_list) + 1
    new_batches = []

    for line in input:
        if batches_generated > max_batches:
            if curr_batch:
                curr_batch.close()
                curr_batch = None
            if line.startswith(tl_node + ': '):
                remaining_hws += 1
        else:
            # FILE MANAGMENT LOGIC
            if line.startswith(tl_node + ': '):
                hw = line.strip('\n').split(': ', 1)[1]
                if hw not in already_exported:
                    hw_idx += 1

                # NEW BATCH FILE
                if hw_idx % batch_size == 0: 
                    if hw_idx > 0:
                        curr_batch.close()

                    batches_generated += 1
                    if batches_generated > max_batches:
                        remaining_hws += 1
                        continue

                    new_filename = batch_dir + '/' + stage + '.batch_%03d.in' % next_batch_num
                    while os.path.exists(new_filename):
                        next_batch_num += 1
                        new_filename = batch_dir + '/' + stage + '.batch_%03d.in' % next_batch_num

                    curr_batch = open(new_filename, 'w')
                    next_batch_num += 1
                    new_batches.append(new_filename)
                    log_info("splitting batches: NO:%d/%d, BATCH: %s" % (batches_generated,  max_batches, new_filename))
            # WRITING TO CURRENT BATCH
            if hw not in already_exported:
                curr_batch.write(line)

    return new_batches, remaining_hws


def update_project_info(batch_size, user, new_batches, project_id, stage, tl_node, remaining_hws, src_dict_id):
    main_db = ops.getMainDB()
    insert_project_dicts = []

    for nvh_file_path in new_batches:
        file_name = nvh_file_path.rsplit('/', 1)[1]

        dict_id = ops.suggestDictId()
        batch_name = file_name.rstrip('.in')

        c = main_db.execute('SELECT * FROM projects WHERE id=?', (project_id,))
        r = c.fetchone()
        language = r['language']

        dictDB = ops.initDict(dict_id, project_id + '.' + batch_name, language, "", user)
        dict_config = {"limits": {"entries": int(batch_size)}}
        ops.attachDict(dictDB, dict_id, {}, dict_config)

        logfile_f = open(os.path.join(siteconfig["dataDir"], 'projects', project_id , stage) + ".log", "a")
        dbpath = os.path.join(siteconfig["dataDir"], "dicts/"+dict_id+".sqlite")
        subprocess.Popen([currdir + "/import.py", dbpath, nvh_file_path, project_id, tl_node],
                          stdout=logfile_f, stderr=logfile_f, start_new_session=True, close_fds=True)


        insert_project_dicts.append((project_id, dict_id, nvh_file_path, stage, 'inProgress'))

    main_db.executemany("INSERT INTO project_dicts (project_id, dict_id, source_nvh, stage, status) VALUES (?,?,?,?,?)", insert_project_dicts)
    c3 = main_db.execute('SELECT remaining FROM project_dicts WHERE dict_id=?', (src_dict_id,))
    r3 = c3.fetchone()
    try:
        is_remaining = json.loads(r3['remaining'])
    except TypeError:
        is_remaining = {}
    is_remaining[stage] = remaining_hws
    main_db.execute('UPDATE project_dicts SET remaining=? WHERE dict_id=?', (json.dumps(is_remaining), src_dict_id))
    main_db.commit()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Split input NVH into batches and import to project')
    parser.add_argument('batch_size', type=int, help='Size of one batch')
    parser.add_argument('max_batches', type=int, help='Number of batches')
    parser.add_argument('generated_batches_filemask', type=str, help='Already annotated batches file mask')
    parser.add_argument('user', type=str, help='User email')
    parser.add_argument('src_dict_id', type=str, help='Source dict id')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input NVH')
    parser.add_argument('--split_only', action='store_true',
                        required=False, default=False,
                        help='Only splits the input nvh into batches without project database update')
    args = parser.parse_args()

    log_start('BATCHES')

    # ==========================
    # INIT
    # ==========================
    batch_list = glob.glob(args.generated_batches_filemask)
    path_spl = args.generated_batches_filemask.split('/')
    batch_dir = '/'.join(path_spl[:-1])
    project_id = path_spl[-3]
    stage = path_spl[-2]
    tl_node = 'entry' # TODO load form db


    if not os.path.exists(batch_dir):
        os.makedirs(batch_dir)
    # ==========================

    # ==========================
    # SPLIT TO BATCHES
    # ==========================
    already_exported = get_already_exported(batch_list, tl_node)
    new_batches, remaining_hws = split_to_batches(args.input, args.max_batches, args.batch_size , batch_list, tl_node, already_exported, batch_dir, stage)
    # ==========================

    # ==========================
    # INSERT TO DB
    # ==========================
    if not args.split_only:
        update_project_info(args.batch_size, args.user, new_batches, project_id, stage, tl_node, remaining_hws, args.src_dict_id.rstrip('.nvh'))

    log_end('BATCHES')


if __name__ == '__main__':
    main()
