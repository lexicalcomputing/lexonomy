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
current_dir = os.path.dirname(os.path.realpath(__file__))


class TestImportNVH(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website

        # LOGIN and get session key
        data = {'email': config.admin_mail,
                'password': config.admin_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email":r1.json()['email'], 'sessionkey':r1.json()['sessionkey']}
        cls.dicID = 'test_import_nvh'
        cls.upload_file_path = ''

    @classmethod
    def update_upload_file_path(cls, value):
        cls.upload_file_path = value

    # DICT CREATE
    def test_1(self):
        data = {'url': self.dicID,
                'hwNode': 'entry',
                'title': self.dicID,
                'addExamples': 'false',
                'deduplicate': 'false',
                'language': 'en',
                'clean': 'on'
                }
        f = open(os.path.join(current_dir, 'test_import.nvh'), 'rb')
        files = {'import_entires': f}

        r = requests.post(url=self.website + "/make.json", data=data, files=files, cookies=self.cookies)
        f.close()
        self.update_upload_file_path(r.json()['upload_file_path'])
        self.assertEqual(r.json()['success'], True)

    def test_2(self):
        data = {'upload_file_path': self.upload_file_path}
        r = requests.post(url=self.website + f"/{self.dicID}/getImportProgress.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['finished'], True)
        self.assertEqual(r.json()['error'], [])
        self.assertEqual(r.json()['progress']['per'], 100)

    def test_3(self):
        data = {'howmany': 100}
        r = requests.post(url=self.website + f"/{self.dicID}/entrylist.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)
        self.assertEqual(r.json()['total'], 5)

    def test_4(self):
        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json",
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)

class TestImportXML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website

        # LOGIN and get session key
        data = {'email': config.admin_mail,
                'password': config.admin_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email":r1.json()['email'], 'sessionkey':r1.json()['sessionkey']}
        cls.dicID = 'test_import_xml'
        cls.upload_file_path = ''
    
    @classmethod
    def update_upload_file_path(cls, value):
        cls.upload_file_path = value

    # DICT CREATE
    def test_1(self):
        data = {'url': self.dicID,
                'hwNode': 'Entry',
                'title': self.dicID,
                'addExamples': 'false',
                'deduplicate': 'false',
                'language': 'en',
                'clean': 'on'
                }
        f = open(os.path.join(current_dir, 'test_import.xml'), 'rb')
        files = {'import_entires': f}

        r = requests.post(url=self.website + "/make.json", data=data, files=files, cookies=self.cookies)
        f.close()
        self.update_upload_file_path(r.json()['upload_file_path'])
        self.assertEqual(r.json()['success'], True)

    def test_2(self):
        data = {'upload_file_path': self.upload_file_path}
        r = requests.post(url=self.website + f"/{self.dicID}/getImportProgress.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['finished'], True)
        self.assertEqual(len(r.json()['warnings']), 0)
        self.assertEqual(r.json()['progress']['per'], 100)

    def test_3(self):
        data = {'howmany': 100}
        r = requests.post(url=self.website + f"/{self.dicID}/entrylist.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)
        self.assertEqual(r.json()['total'], 3)

    def test_4(self):
        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json", 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)

class TestImportToExisting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {"Content-type": "application/json", "Accept": "text/plain"}
        cls.website = config.website

        # LOGIN and get session key
        data = {"email": config.admin_mail, "password": config.admin_password}

        r1 = requests.post(
            url=cls.website + "/login.json", data=data, headers=cls.headers
        )
        cls.cookies = {
            "email": r1.json()["email"],
            "sessionkey": r1.json()["sessionkey"],
        }
        cls.dicID = "test_import_nvh_to_existing"
        cls.upload_file_path = ""

    @classmethod
    def update_upload_file_path(cls, value):
        cls.upload_file_path = value

    # DICT CREATE
    def test_1(self):
        data = {
            "url": self.dicID,
            "title": self.dicID,
            "addExamples": "false",
            "deduplicate": "false",
            "language": "en",
            "structure": json.dumps(
                {
                    "nvhSchema":
                    "entry: + string\n"
                    "  hw: string\n"
                    "  lemma: string\n"
                    "  pos: string\n"
                    "  sense: * string\n"
                    "    image: + image\n"
                    "      license: string\n"
                    "      source: string\n"
                    "      quality: string\n"
                    "      author: string\n"
                    "      explicit: bool\n"
                    "    example: * string\n"
                    "      quality: ? string\n"
                    "      en_translation: string\n"
                    "      cs_translation: ? string\n"
                    "      de_translation: ? string\n"
                    "  rank: string\n"
                    "  flag: string\n"
                    "  notes: string\n"
                    "  prefix_sense: ? string\n"
                    "  example: * string\n"
                }
            ),
        }

        r = requests.post(
            url=self.website + "/make.json", data=data, cookies=self.cookies
        )
        self.assertEqual(r.json()["success"], True)

    def test_2(self):
        data = {
            "purge": "false",
            "deduplicate": "false",
            "purge_all": "false",
            "hwNode": "entry",
        }
        f = open(os.path.join(current_dir, "test_import.nvh"), "rb")
        files = {"import_entires": f}
        r = requests.post(
            url=self.website + f"/{self.dicID}/import.json",
            data=data,
            files=files,
            cookies=self.cookies,
        )
        f.close()
        self.update_upload_file_path(r.json()["upload_file_path"])

    def test_3(self):
        data = {"upload_file_path": self.upload_file_path}
        r = requests.post(
            url=self.website + f"/{self.dicID}/getImportProgress.json",
            data=data,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["finished"], True)
        self.assertEqual(r.json()["error"], [])
        self.assertEqual(r.json()["progress"]["per"], 100)

    def test_3(self):
        data = {"howmany": 100}
        r = requests.post(
            url=self.website + f"/{self.dicID}/entrylist.json",
            data=data,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)
        self.assertEqual(r.json()["total"], 5)

    def test_4(self):
        r = requests.post(
            url=self.website + "/" + self.dicID + "/destroy.json",
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)


if __name__ == '__main__':
    unittest.main()
