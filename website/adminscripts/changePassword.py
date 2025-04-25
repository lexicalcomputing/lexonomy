#!/usr/bin/env python3

import json
import sys
import os.path
import sqlite3
import hashlib
import random
import string

if len(sys.argv) != 2:
    print("This tool changes the password for user with a given email")
    print("Usage: ./adminscripts/changePassword.py email")
    sys.exit()

main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
siteconfig_file_path = os.path.join(main_dir, "siteconfig.json")
siteconfig = json.load(open(siteconfig_file_path, encoding="utf-8"))
path = os.path.join(siteconfig["dataDir"], 'lexonomy.sqlite')
conn = sqlite3.connect(path)
print("Connected to database: %s" % path)

email = sys.argv[1];
password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
try:
    conn.execute("update users set passwordHash=? where email=?", (passhash, email))
    conn.commit()
    print("User %s now has a new password: %s" % (email, password))
except sqlite3.Error as e:
    print("Could not update password for user %s. Database error: %s" % (email, e))

conn.close() 

