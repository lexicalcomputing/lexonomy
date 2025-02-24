#!/usr/bin/env python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import sys
import config
import requests
import unittest
# Append the parent directory to the system path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
current_dir = os.path.dirname(os.path.realpath(__file__))


class TestDictFromFiles(unittest.TestCase):
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
        cls.dicID = 'test_dict_from_files'
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
        enties_f = open(os.path.join(current_dir, 'new_dict_from_template', 'entries.nvh'), 'rb')
        config_f = open(os.path.join(current_dir, 'new_dict_from_template', 'configs.json'), 'rb')
        ce_css_f = open(os.path.join(current_dir, 'new_dict_from_template', 'custom_editor.css'), 'rb')
        ce_js_f = open(os.path.join(current_dir, 'new_dict_from_template', 'custom_editor.js'), 'rb')
        structure_f = open(os.path.join(current_dir, 'new_dict_from_template', 'structure.nvh'), 'rb')
        styles_f = open(os.path.join(current_dir, 'new_dict_from_template', 'styles.css'), 'rb')

        files = {'import_entries': enties_f,
                 'config': config_f,
                 'ce_css': ce_css_f,
                 'ce_js': ce_js_f,
                 'structure': structure_f,
                 'styles': styles_f}

        r = requests.post(url=self.website + "/make.json", data=data, files=files, cookies=self.cookies)
        # close files
        for i in [enties_f, config_f, ce_css_f, ce_js_f, structure_f, styles_f]:
            i.close()

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
        self.assertEqual(r.json()['total'], 5)

    def test_4(self):
        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json",
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)

class TestTemplatedDict(unittest.TestCase):
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
        cls.dicID = 'test_dict_from_template'
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
                'clean': 'on',
                'template_id': 'general'
                }

        r = requests.post(url=self.website + "/make_templated.json", data=data, cookies=self.cookies)
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
        self.assertEqual(r.json()['total'], 5)

    def test_4(self):
        r = requests.post(url=self.website + '/' + self.dicID + "/destroy.json", 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)


if __name__ == '__main__':
    unittest.main()
