#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Assign dict to user with specified access rights')
    parser.add_argument('dict_id', type=str,
                        help='Dictionary ID')
    parser.add_argument('email', type=str,
                        help='Assignee email')
    parser.add_argument('access_rights', type=str,
                        help='Access rights.\n'
                        'OPTIONS read:r, write:w, config:c, download:d, upload:u')
    
    args = parser.parse_args()

    can_read = 1 if 'r' in args.access_rights else 0
    can_write = 1 if 'w' in args.access_rights else 0
    can_config = 1 if 'c' in args.access_rights else 0
    can_download = 1 if 'd' in args.access_rights else 0
    can_upload = 1 if 'u' in args.access_rights else 0

    conn = ops.getMainDB()
    r1 = conn.execute("SELECT dict_id, user_email FROM user_dict WHERE dict_id=? AND user_email=?", (args.dict_id, args.email.lower()))
    if r1.fetchone:
        if can_read + can_write + can_config + can_download + can_upload == 0:
            conn.execute("DELETE FROM user_dict WHERE dict_id=? AND user_email=?", (args.dict_id, args.email.lower()))
        else:
            conn.execute("UPDATE user_dict SET can_view=?, can_edit=?, can_config=?, can_download=?, can_upload=? WHERE dict_id=? AND user_email=?", 
                        (can_read, can_write, can_config, can_download, can_upload, args.dict_id, args.email.lower()))
    else:
        conn.execute("INSERT INTO user_dict (dict_id, user_email, can_view, can_edit, can_config, can_download, can_upload) values (?,?,?,?,?,?,?)",
                     (args.dict_id, args.email.lower(), can_read, can_write, can_config, can_download, can_upload))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()