#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import json
import config
import requests
import unittest

# Append the parent directory to the system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ops import getDB

current_dir = os.path.dirname(os.path.realpath(__file__))


class TestDictAccessPublic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {"Content-type": "application/json", "Accept": "text/plain"}
        cls.website = config.website
        cls.dicID = "test_dict_access_nvh"

    def test_1(self):
        ####################
        # LOGIN AS ADMIN
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.admin_mail, "password": config.admin_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        ####################
        # CREATE DICT AS ADMIN
        ####################
        data = {
            "url": self.dicID,
            "hwNode": "entry",
            "title": self.dicID,
            "addExamples": "false",
            "deduplicate": "false",
            "language": "en",
            "clean": "on",
        }
        f = open(os.path.join(current_dir, "test_import.nvh"), "rb")
        files = {"import_entries": f}

        r = requests.post(
            url=self.website + "/make.json", data=data, files=files, cookies=cookies
        )
        f.close()
        self.assertEqual(r.json()["success"], True)

        conn = getDB(self.dicID)
        conn.execute(
            "UPDATE configs SET json=? WHERE id=?",
            (json.dumps({"public": True}), "publico"),
        )
        conn.commit()

    def test_2(self):
        ####################
        # LOGIN AS STANDARD USER
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.user_mail, "password": config.user_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        ####################
        # CONFIG
        ####################
        r1 = requests.get(
            url=self.website + f"/{self.dicID}/config.json",
            headers=self.headers,
            cookies=cookies,
        )
        self.assertTrue(r1.json()['configs']['publico']['public'])
        self.assertTrue(r1.json()['userAccess']['canView'])

        ####################
        # ENTRYLIST
        ####################
        r2 = requests.post(
            url=self.website + f"/{self.dicID}/entrylist.json",
            data={"howmany": 100},
            cookies=cookies,
        )
        self.assertEqual(len(r2.json()['entries']), 5)

        ####################
        # RANDOM
        ####################
        r3 = requests.post(
            url=self.website + f"/{self.dicID}/random.json",
            cookies=cookies,
        )
        self.assertEqual(len(r3.json()['entries']), 5)

        ####################
        # ENTRYREAD
        ####################
        r4 = requests.post(
            url=self.website + f"/{self.dicID}/entryread.json",
            data={"id": 1},
            cookies=cookies,
        )
        self.assertTrue(r4.json()['success'])
        self.assertTrue('lemma: test_1' in r4.json()['nvh'])

    def test_3(self):
        ####################
        # DELETE DICT AS ADMIN
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.admin_mail, "password": config.admin_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json",
                          headers=self.headers, cookies=cookies)
        self.assertEqual(r.json()['success'], True)


class TestDictAccessPrivate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {"Content-type": "application/json", "Accept": "text/plain"}
        cls.website = config.website
        cls.dicID = "test_dict_access_nvh"

    def test_1(self):
        ####################
        # LOGIN AS ADMIN
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.admin_mail, "password": config.admin_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        ####################
        # CREATE DICT AS ADMIN
        ####################
        data = {
            "url": self.dicID,
            "hwNode": "entry",
            "title": self.dicID,
            "addExamples": "false",
            "deduplicate": "false",
            "language": "en",
            "clean": "on",
        }
        f = open(os.path.join(current_dir, "test_import.nvh"), "rb")
        files = {"import_entries": f}

        r = requests.post(
            url=self.website + "/make.json", data=data, files=files, cookies=cookies
        )
        f.close()
        self.assertEqual(r.json()["success"], True)

    def test_2(self):
        ####################
        # LOGIN AS STANDARD USER
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.user_mail, "password": config.user_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        ####################
        # CONFIG
        ####################
        r1 = requests.get(
            url=self.website + f"/{self.dicID}/config.json",
            headers=self.headers,
            cookies=cookies,
        )
        self.assertFalse(r1.json()['configs']['publico']['public'])
        self.assertFalse(r1.json()['userAccess']['canView'])

        ####################
        # ENTRYLIST
        ####################
        r2 = requests.post(
            url=self.website + f"/{self.dicID}/entrylist.json",
            data={"howmany": 100},
            cookies=cookies,
        )
        self.assertFalse(r2.json()['dictAccess']['canView'])
        self.assertFalse(r2.json()['dictAccess']['canEdit'])
        self.assertFalse(r2.json()['dictAccess']['canConfig'])
        self.assertFalse(r2.json()['dictAccess']['canDownload'])
        self.assertFalse(r2.json()['dictAccess']['canUpload'])

        ####################
        # RANDOM
        ####################
        r3 = requests.post(
            url=self.website + f"/{self.dicID}/random.json",
            cookies=cookies,
        )
        self.assertFalse(r3.json()['dictAccess']['canView'])
        self.assertFalse(r3.json()['dictAccess']['canEdit'])
        self.assertFalse(r3.json()['dictAccess']['canConfig'])
        self.assertFalse(r3.json()['dictAccess']['canDownload'])
        self.assertFalse(r3.json()['dictAccess']['canUpload'])

        ####################
        # ENTRYREAD
        ####################
        r4 = requests.post(
            url=self.website + f"/{self.dicID}/entryread.json",
            data={"id": 1},
            cookies=cookies,
        )
        self.assertFalse(r4.json()['dictAccess']['canView'])
        self.assertFalse(r4.json()['dictAccess']['canEdit'])
        self.assertFalse(r4.json()['dictAccess']['canConfig'])
        self.assertFalse(r4.json()['dictAccess']['canDownload'])
        self.assertFalse(r4.json()['dictAccess']['canUpload'])


    def test_3(self):
        ####################
        # DELETE DICT AS ADMIN
        ####################
        r0 = requests.post(
            url=self.website + "/login.json",
            data={"email": config.admin_mail, "password": config.admin_password},
            headers=self.headers,
        )
        cookies = {"email": r0.json()["email"], "sessionkey": r0.json()["sessionkey"]}

        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json",
                          headers=self.headers, cookies=cookies)
        self.assertEqual(r.json()['success'], True)

if __name__ == '__main__':
    unittest.main()