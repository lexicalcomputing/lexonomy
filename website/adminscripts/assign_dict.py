#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops


def main():
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Assign dict to user with specified access rights.\n\n'
                                                 'EXAMPLE USAGE:\n'
                                                 'FULL ACCESS: ./assign_dict.py test test@localhost -a canView canEdit canAdd canDelete canEditSource canConfig canDownload canUpload\n'
                                                 'PARTIAL ACCESS: ./assign_dict.py test test@localhost -a canView canEdit canAdd canDelete\n'
                                                 'DELETE ACCESS: ./assign_dict.py test test@localhost')
    parser.add_argument('dict_id', type=str,
                        help='Dictionary ID')
    parser.add_argument('email', type=str,
                        help='Assignee email')
    parser.add_argument('-a', '--access_rights', type=str, nargs='*', default=[],
                        help='Access rights.\n'
                        'OPTIONS: canView, canEdit, canAdd, canDelete, canEditSource, canConfig, canDownload, canUpload')
    
    args = parser.parse_args()

    can_view = 1 if 'canView' in args.access_rights else 0
    can_edit = 1 if 'canEdit' in args.access_rights else 0
    can_add = 1 if 'canAdd' in args.access_rights else 0
    can_delete = 1 if 'canDelete' in args.access_rights else 0
    can_edit_source = 1 if 'canEditSource' in args.access_rights else 0
    can_config = 1 if 'canConfig' in args.access_rights else 0
    can_download = 1 if 'canDownload' in args.access_rights else 0
    can_upload = 1 if 'canUpload' in args.access_rights else 0

    conn = ops.getMainDB()
    r1 = conn.execute("SELECT dict_id, user_email FROM user_dict WHERE dict_id=? AND user_email=?", (args.dict_id, args.email.lower()))
    if r1.fetchone():
        if can_view + can_edit + can_add + can_delete + can_edit_source + can_config + can_download + can_upload == 0:
            conn.execute("DELETE FROM user_dict WHERE dict_id=? AND user_email=?", (args.dict_id, args.email.lower()))
        else:
            conn.execute("UPDATE user_dict SET canView=?, canEdit=?, canAdd=?, canDelete=?, canEditSource=?, canConfig=?, canDownload=?, canUpload=? WHERE dict_id=? AND user_email=?", 
                        (can_view, can_edit, can_add, can_delete, can_edit_source, can_config, can_download, can_upload, args.dict_id, args.email.lower()))
    else:
        conn.execute("INSERT INTO user_dict (dict_id, user_email, canView, canEdit, canAdd, canDelete, canEditSource, canConfig, canDownload, canUpload) values (?,?,?,?,?,?,?,?,?,?)",
                     (args.dict_id, args.email.lower(), can_view, can_edit, can_add, can_delete, can_edit_source, can_config, can_download, can_upload))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()