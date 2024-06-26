#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import config
import requests
import unittest
sys.path.append('../')
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
        files = {'filename': f}

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
        r = requests.post(url=self.website + f"/{self.dicID}/entry/entrylist.json", data=data, cookies=self.cookies)
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
                'hwNode': 'entry',
                'title': self.dicID,
                'addExamples': 'false',
                'deduplicate': 'false',
                'language': 'en',
                'clean': 'on'
                }
        f = open(os.path.join(current_dir, 'test_import.xml'), 'rb')
        files = {'filename': f}

        r = requests.post(url=self.website + "/make.json", data=data, files=files, cookies=self.cookies)
        f.close()
        self.update_upload_file_path(r.json()['upload_file_path'])
        self.assertEqual(r.json()['success'], True)

    def test_2(self):
        data = {'upload_file_path': self.upload_file_path}
        r = requests.post(url=self.website + f"/{self.dicID}/getImportProgress.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['finished'], True)
        self.assertEqual(len(r.json()['warnings']), 11)
        self.assertEqual(r.json()['progress']['per'], 100)

    def test_3(self):
        data = {'howmany': 100}
        r = requests.post(url=self.website + f"/{self.dicID}/entry/entrylist.json", data=data, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)
        self.assertEqual(r.json()['total'], 3)

    def test_4(self):
        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json", 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)


if __name__ == '__main__':
    unittest.main()
