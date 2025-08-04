#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ops import getMainDB


def main():
    import argparse
    parser = argparse.ArgumentParser(description='This script adds new workflow to lexonomy DB and copy workflow to correct destination')
    parser.add_argument('new_workflow_dir', type=str,
                        help='Workflow to import')
    parser.add_argument('-d', '--description', type=str, required=False, default='',
                        help='Workflow description')
    parser.add_argument('-n', '--name', type=str, required=False, default='',
                        help='Workflow name')
    parser.add_argument('-f', '--force', action='store_true', required=False, default=False,
                        help='Force rewrite')
    args = parser.parse_args()

    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow_id = args.new_workflow_dir.strip().rstrip('/').split('/')[-1]
    app_workflow_dir = os.path.join(main_dir, 'workflows', workflow_id)

    try:
        shutil.copytree(args.new_workflow_dir, app_workflow_dir, dirs_exist_ok=args.force)
        print(f"Directory '{args.new_workflow_dir}' successfully copied to '{app_workflow_dir}'")
    except FileExistsError:
        print(f"Error: Destination directory '{app_workflow_dir}' already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")

    workflow_name = args.name if args.name else workflow_id

    main_db = getMainDB()
    r = main_db.execute('SELECT * FROM workflows WHERE id=?', (workflow_id,))
    if r.fetchone():
        if args.force:
            main_db.execute('UPDATE workflows SET name=?, description=? WHERE id=?', (workflow_name, args.description, workflow_id))
    else:
        main_db.execute('INSERT INTO workflows (id, name, description) VALUES (?,?,?)', (workflow_id, workflow_name, args.description))
    main_db.commit()
    main_db.close()


if __name__ == '__main__':
    main()

