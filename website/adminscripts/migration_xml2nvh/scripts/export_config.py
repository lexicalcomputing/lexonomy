#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json
import sqlite3
from collections import defaultdict

defaultDictConfig = {"editing": {"xonomyMode": "nerd", "xonomyTextEditor": "askString" },
                     "searchability": {"searchableElements": []},
                     "xema": {"elements": {}},
                     "titling": {"headwordAnnotations": []},
                     "flagging": {"flag_element": "", "flags": []},
                     "limits": {"entries": 5000}}


def getDB(path, dictID):
    conn = sqlite3.connect(os.path.join(path, dictID+".sqlite"))
    conn.row_factory = sqlite3.Row
    conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on")
    return conn


def readDictConfigs(dictDB):
    configs = {}
    c = dictDB.execute("select * from configs")
    for r in c.fetchall():
        configs[r["id"]] = json.loads(r["json"])
    for conf in ["ident", "publico", "users", "kex", "kontext", "titling", "flagging",
                 "searchability", "xampl", "thes", "collx", "defo", "xema",
                 "xemplate", "editing", "subbing", "download", "links", "autonumber", "gapi", "metadata"]:
        if not conf in configs:
            configs[conf] = defaultDictConfig.get(conf, {})

    users = {}
    for email in configs["users"]:
        users[email.lower()] = configs["users"][email]
    configs["users"] = users

    for key in configs.keys():
        if type(configs[key]) is dict:
            configs[key] = defaultdict(lambda: None, configs[key])

    return configs


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Export config of specified dict')
    parser.add_argument('-d', '--dicts', type=str,
                        required=True,
                        help="Path do dict's sqlite dir")
    parser.add_argument('-i', '--input', type=argparse.FileType('r'),
                        required=False, default=sys.stdin,
                        help='Input')
    parser.add_argument('-o', '--output', type=str,
                        required=True,
                        help='Output dir')
    args = parser.parse_args()


    for dictID in args.input:
        dictID = dictID.strip()
        try:
            conn = getDB(args.dicts, dictID)
            config = readDictConfigs(conn)
            with open(os.path.join(args.output, dictID+'.json.orig'), 'w') as j_out:
                json.dump(config, j_out, indent = 4)

        except Exception as e:
            sys.stderr.write(f'Error: {dictID}: {e}\n')


if __name__ == '__main__':
    main()

