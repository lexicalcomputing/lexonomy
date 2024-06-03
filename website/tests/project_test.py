#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import requests
import json
import unittest
import config
import time
import random
from pprint import pprint
current_dir = os.path.dirname(os.path.realpath(__file__))


class TestQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verbose = False
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website

        # LOGIN and get session key
        data = {'email': config.admin_mail,
                'password': config.admin_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email":r1.json()['email'], 'sessionkey':r1.json()['sessionkey']}

        # generate project id
        r2 = requests.get(url=cls.website + "/projects/suggestid.json",
                          headers=cls.headers, cookies=cls.cookies)
        cls.new_project_id = r2.json()['suggested']

        # get workflow name
        # r3 = requests.get(url=cls.website + "/wokflows/list.json",
        #                   headers=cls.headers, cookies=cls.cookies)
        cls.workflow = 'test_workflow_new'

        cls.source_dict_id = ''
        cls.batch_log_file = ''
        cls.all_batches_dict_ids = []

        # TODO RM
        cls.source_dict_id = 'marek_project_dict'
        cls.new_project_id = 'marek_project'

    @classmethod
    def update_source_dict(cls, value):
        cls.source_dict_id = value

    @classmethod
    def update_batch_log_file(cls, value):
        cls.batch_log_file = value

    @classmethod
    def update_all_batches(cls):
        API_ENDPOINT_0 = cls.website + f"/projects/{cls.new_project_id}/project.json"
        r0 = requests.get(url=API_ENDPOINT_0, headers=cls.headers, cookies=cls.cookies)

        for stage in r0.json()['workflow']:
            for batch_dict in stage['batches']:
                cls.all_batches_dict_ids.append((stage['stage'], batch_dict['dictID'], batch_dict['title']))

    # SOURCE DICT CREATE
    def test_1(self):
        data = {'url': self.source_dict_id,
                'hwNode': 'entry',
                'title': self.source_dict_id,
                'addExamples': 'false',
                'deduplicate': 'false',
                'language': 'en'
                }
        f = open(os.path.join(current_dir, 'example_nvh', 'project_source.nvh'), 'rb')
        files = {'filename': f}

        r = requests.post(url=self.website + "/make.json", data=data, files=files, cookies=self.cookies)
        f.close()

        if self.verbose:
            print('================================')
            print('CREATE DICT')
            print('================================')
            pprint(r.json())

        self.assertEqual(r.json()['success'], True)
        self.update_source_dict(r.json()['url'])

    # CREATE PROJECT
    def test_2(self):
        API_ENDPOINT_1 = self.website + "/projects/create.json"
        data = {'id': self.new_project_id,
                'name': 'LCL test project',
                'description': 'This is a testing project',
                'annotators': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']),
                'managers': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']),
                'ref_corpus': 'ententen21_tt31',
                'source_dict_id': self.source_dict_id,
                'workflow': self.workflow,
                'language': 'cs'}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        self.assertEqual(r1.json()['projectID'], self.new_project_id)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)

        if self.verbose:
            print('================================')
            print('CREATE PROJECT')
            print('================================')
            pprint(r2.json())

        self.assertEqual(r2.json()['description'], 'This is a testing project')
        self.assertEqual(set(r2.json()['managers']) - set(["marek.medved3@gmail.com", "marek.medved@sketchengine.co.uk", "marek.medved@sketchengine.eu"]), set())
        self.assertEqual(set(r2.json()['annotators']) - set(["marek.medved3@gmail.com", "marek.medved@sketchengine.co.uk", "marek.medved@sketchengine.eu"]), set())
        # ================

        # ================
        # IN PROJECT LISTING
        # ================
        API_ENDPOINT_3 = self.website + "/projects/list.json"
        r3 = requests.get(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)
        found = False
        for x in r3.json()['projects_active']:
            if x['id'] == self.new_project_id:
                found = True
        self.assertEqual(found, True)
        # ================

    # EDIT PROJECT
    def test_3(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/update.json"
        data = {'name': 'LCL test project updated',
                'description': 'This is a testing project updated',
                'annotators': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.co.uk', 'xmedved1.fi.muni.cz']),
                'managers': json.dumps(['marek.medved@sketchengine.eu']),
                }
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)

        if self.verbose:
            print('================================')
            print('EDIT PROJECT')
            print('================================')
            pprint(r2.json())

        self.assertEqual(r2.json()['description'], 'This is a testing project updated')
        self.assertEqual(set(r2.json()['managers']) - set(["marek.medved@sketchengine.eu"]), set())
        self.assertEqual(set(r2.json()['annotators']) - set(['marek.medved3@gmail.com', 'marek.medved@sketchengine.co.uk', 'xmedved1.fi.muni.cz']), set())
        # ================

    # CREATE BATCH
    def test_4(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/create_batch.json"
        data = {'stage': 'sensitive',
                'size': 1,
                'batch_number': 3,
                }
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/create_batch.json"
        data = {'stage': 'images',
                'size': 1,
                'batch_number': 3,
                }
        r2 = requests.post(url=API_ENDPOINT_2, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['success'], True)

        # TODO
        # API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/getBatchesStatus.json"
        # data = {'stage': 'sensitive'}
        # r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        # self.assertEqual(r2.json()['description'], 'This is a testing project updated')
        # self.assertEqual(set(r2.json()['managers']) - set(["marek.medved@sketchengine.eu"]), set())
        # self.assertEqual(set(r2.json()['annotators']) - set(['marek.medved3@gmail.com', 'marek.medved@sketchengine.co.uk', 'marek.medved@sketchengine.eu', 'xmedved1.fi.muni.cz']), set())

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_3 = self.website + f"/projects/{self.new_project_id}/project.json"
        r3 = requests.get(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)

        if self.verbose:
            print('================================')
            print('CREATE BATCH')
            print('================================')
            pprint(r3.json())

        self.assertEqual(r3.json()['workflow'][0]['batches'][0]['nvh'].rsplit('/',1)[1], 'sensitive.batch_001.in')
        self.assertEqual(r3.json()['workflow'][0]['batches'][0]['status'], 'inProgress')
        self.assertEqual(r3.json()['workflow'][0]['batches'][0]['assignee'], None)
        self.assertEqual(r3.json()['workflow'][0]['inputDicts'][0]['remaining'], 2)

        self.assertEqual(r3.json()['workflow'][1]['batches'][0]['nvh'].rsplit('/',1)[1], 'images.batch_001.in')
        self.assertEqual(r3.json()['workflow'][1]['batches'][0]['status'], 'inProgress')
        self.assertEqual(r3.json()['workflow'][1]['batches'][0]['assignee'], None)
        self.assertEqual(r3.json()['workflow'][1]['inputDicts'][0]['remaining'], 2)
        # ================

        # get dicIDs of all batches
        self.update_all_batches()

    # ASSIGN BATCH
    def test_5(self):
        # ================
        # ASSIGN ALL BATCHES 
        # ================
        API_ENDPOINT_1 = self.website + f"projects/{self.new_project_id}/assign_batch.json"
        data = {'assignees': json.dumps([(x[1], "marek.medved@sketchengine.eu") for x in self.all_batches_dict_ids])}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        # ================
        # ANNOTATE dicts
        # ================
        sensitive_values = ['yes', 'no']
        images_values = ['my_image.jpg', 'this_image.svg', 'just_image.png']
        for s, dict_id, title in self.all_batches_dict_ids:
            API_ENDPOINT_2 = self.website + f"{dict_id}/entryread.json"
            data = {'id': 1}
            r2 = requests.post(url=API_ENDPOINT_2, data=data, headers=self.headers, cookies=self.cookies)

            if s == 'sensitive':
                annot_nvh = str(r2.json()['nvh']) + \
                            f'    sensitive: {random.choice(sensitive_values)}\n' + \
                            f'    __lexonomy_completed__: {title}\n'
            elif s == 'images':
                annot_nvh = str(r2.json()['nvh']) + \
                            f'    image: {random.choice(images_values)}\n' + \
                            f'    __lexonomy_completed__: {title}\n'
            else:
                annot_nvh = str(r2.json()['nvh']) + \
                            f'   __lexonomy_completed__: {title}\n'

            API_ENDPOINT_3 = self.website + f"{dict_id}/entryupdate.json"
            data = {'id': 1,
                    'nvh': annot_nvh}
            r3 = requests.post(url=API_ENDPOINT_3, data=data, headers=self.headers, cookies=self.cookies)
            self.assertEqual(r3.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_4 = self.website + f"/projects/{self.new_project_id}/project.json"
        r4 = requests.get(url=API_ENDPOINT_4, headers=self.headers, cookies=self.cookies)

        if self.verbose:
            print('================================')
            print('ASSIG BATCH')
            print('================================')
            pprint(r4.json())

        self.assertEqual(r4.json()['workflow'][0]['batches'][0]['assignee'], 'marek.medved@sketchengine.eu')
        # ================

    # REJECT BATCH
    def test_6(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/reject_batch.json"
        data = {'dictID_list': json.dumps([self.all_batches_dict_ids[0][1]])}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)

        if self.verbose:
            print('================================')
            print('REJECT BATCH')
            print('================================')
            pprint(r2.json())

        for s in r2.json()['workflow']:
            for b in s['batches']:
                if b['dictID'] == self.all_batches_dict_ids[0][1]:
                    self.assertEqual(b['status'], 'rejected')
                    self.assertTrue(b['nvh'].endswith('.rejected'))
        # ================

    # ACCEPT BATCH
    def test_7(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/accept_batch.json"
        data = {'dictID_list': json.dumps([x[1] for x in self.all_batches_dict_ids])}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('ACCEPT BATCH')
            print('================================')
            pprint(r2.json())

        for s in r2.json()['workflow']:
            for b in s['batches']:
                self.assertEqual(b['status'], 'accepted')
        # ================

    # MERGE SENSITIVE/IMAGES
    def test_8(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/make_stage.json"
        data = {'stage': 'sensitive'}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/make_stage.json"
        data = {'stage': 'images'}
        r2 = requests.post(url=API_ENDPOINT_2, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['success'], True)

        API_ENDPOINT_3 = self.website + f"/projects/{self.new_project_id}/make_stage.json"
        data = {'stage': 'final'}
        r3 = requests.post(url=API_ENDPOINT_3, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r3.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_4 = self.website + f"/projects/{self.new_project_id}/project.json"
        r4 = requests.get(url=API_ENDPOINT_4, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('MERGE SENSITIVE')
            print('================================')
            pprint(r4.json())

    # DELETE PROJECT
    def test_9(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/delete.json"
        r1 = requests.post(url=API_ENDPOINT_1, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        self.assertEqual(r1.json()['projectID'], self.new_project_id)

        # ================
        # PROJECT DELETED FORM PROJECT LIST
        # ================
        API_ENDPOINT_2 = self.website + "/projects/list.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['projects_active'], [])
        self.assertEqual(r2.json()['projects_archived'], [])
        self.assertEqual(r2.json()['total'], 0)
        # ================


if __name__ == '__main__':
    unittest.main()