#!/usr/bin/python3.10
# coding: utf-8
# usage: project_gen_next_batch.py BATCH_SIZE [MAX_BATCHES] [EXISTING_BATCHES_FILEMASK] [USER_EMAIL]
import os
import sys
import glob
import json
import ops
import project
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
        if line.strip():
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


def update_remaining(project_id, stage, remaining_hws):
    project_targets, _, _ = project.getMakeDeps(project_id)
    if len(project_targets[stage]) > 1:
        log_err('project_targets has more than one dependency')
        return

    main_db = ops.getMainDB()
    c2 = main_db.execute('SELECT remaining FROM project_dicts WHERE stage=? AND project_id=?', (project_targets[stage][0], project_id))
    r2 = c2.fetchone()

    try:
        is_remaining = json.loads(r2['remaining'])
    except TypeError:
        is_remaining = {}
    is_remaining[stage] = remaining_hws
    main_db.execute('UPDATE project_dicts SET remaining=? WHERE stage=? AND project_id=?', (json.dumps(is_remaining), project_targets[stage][0], project_id))
    main_db.commit()
    main_db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Split input NVH into batches and import to project')
    parser.add_argument('batch_size', type=int, help='Size of one batch')
    parser.add_argument('max_batches', type=int, help='Number of batches')
    parser.add_argument('generated_batches_filemask', type=str, help='Already annotated batches file mask')
    parser.add_argument('tl_node', type=str, help='Top level NVh node (main entry node)')
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input NVH')
    args = parser.parse_args()

    log_start('BATCHES')

    # ==========================
    # INIT
    # ==========================
    batch_list = glob.glob(args.generated_batches_filemask)
    path_spl = args.generated_batches_filemask.split('/')
    batch_dir = '/'.join(path_spl[:-1])
    stage = path_spl[-2]
    project_id = path_spl[-3]

    if not os.path.exists(batch_dir):
        os.makedirs(batch_dir)
    # ==========================

    # ==========================
    # SPLIT TO BATCHES
    # ==========================
    already_exported = get_already_exported(batch_list, args.tl_node)
    new_batches, remaining_hws = split_to_batches(args.input, args.max_batches, args.batch_size , batch_list, args.tl_node, already_exported, batch_dir, stage)
    if new_batches:
        update_remaining(project_id, stage, remaining_hws)

        for batch_name in new_batches:
            sys.stdout.write(f'{batch_name}\n')
    else:
        log_warning(f'Project {project_id} - no new batches created, due to empty list of suitable entries for given stage {stage}.')

    log_end('BATCHES')


if __name__ == '__main__':
    main()
