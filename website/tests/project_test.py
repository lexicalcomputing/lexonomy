#!/usr/bin/python3.10
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import os
import requests
import json
import unittest
import config
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
        cls.workflow = 'test_workflow_1'

        cls.source_dict_id = ''
        cls.batch_log_file = ''
        cls.all_batches_dict_ids = set()

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
            if stage['is_locked']:
                cls.update_all_batches()
            else:
                for batch_dict in stage['batches']:
                    cls.all_batches_dict_ids.add((stage['stage'], batch_dict['dictID'], batch_dict['title']))

    # SOURCE DICT CREATE
    def test_01(self):
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
    def test_02(self):
        API_ENDPOINT_1 = self.website + "/projects/create.json"
        data = {'id': self.new_project_id,
                'name': 'LCL test project',
                'description': 'This is a testing project',
                'annotators': json.dumps({'__all__': ['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']}),
                'managers': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']),
                'ref_corpus': 'ententen21_tt31',
                'source_dict_id': self.source_dict_id,
                'workflow_id': self.workflow,
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
        # ================

        # ================
        # IN PROJECT LISTING
        # ================
        API_ENDPOINT_3 = self.website + "/projects/list.json"
        r3 = requests.get(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)
        found = False
        for x in r3.json()['projects_active']:
            if x['projectID'] == self.new_project_id:
                found = True
        self.assertEqual(found, True)
        # ================

    # EDIT PROJECT
    def test_03(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/update.json"
        data = {'name': 'LCL test project updated',
                'description': 'This is a testing project updated',
                'annotators': json.dumps({'sensitive': ['marek.medved3@gmail.com', 'marek.medved@sketchengine.co.uk', 'xmedved1.fi.muni.cz']}),
                'managers': json.dumps(['marek.medved@sketchengine.eu'])}
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
        # ================

    # CREATE BATCH
    def test_04(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/create_batch.json"
        data = {'stage': 'sensitive',
                'size': 1,
                'batch_number': 4,
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
        # ================

        # ================
        # DELETE ONE BATCH
        # ================
        API_ENDPOINT_4 = self.website + f"/projects/{self.new_project_id}/delete_batch.json"
        data = {'dictID_list': json.dumps([r3.json()['workflow'][0]['batches'][3]['dictID']])}
        r4 = requests.post(url=API_ENDPOINT_4, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r4.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_5 = self.website + f"/projects/{self.new_project_id}/project.json"
        r5 = requests.get(url=API_ENDPOINT_5, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('DELETE BATCH')
            print('================================')
            pprint(r5.json())

        self.assertTrue('marek_project.sensitive.batch' in r5.json()['workflow'][0]['batches'][0]['title'])
        self.assertTrue(r5.json()['workflow'][0]['batches'][0]['status'] in ['inProgress', 'creating'])
        self.assertEqual(r5.json()['workflow'][0]['batches'][0]['assignee'], None)
        self.assertEqual(r5.json()['workflow'][0]['inputDicts'][0]['remaining'], 2)
        # ================

    # ASSIGN BATCH
    def test_05(self):
        # get dicIDs of all batches
        self.update_all_batches()
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
                            f'    __lexonomy__completed: {title}\n'
            elif s == 'images':
                annot_nvh = str(r2.json()['nvh']) + \
                            f'    image: {random.choice(images_values)}\n' + \
                            f'    __lexonomy__completed: {title}\n'
            else:
                annot_nvh = str(r2.json()['nvh']) + \
                            f'   __lexonomy__completed: {title}\n'

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
    def test_06(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/reject_batch.json"
        batch_dic_ids = [x[1] for x in self.all_batches_dict_ids if x[2] == 'marek_project.sensitive.batch_001']
        data = {'dictID_list': json.dumps(batch_dic_ids)}
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
                if b['dictID'] == batch_dic_ids[0]:
                    self.assertEqual(b['status'], 'rejected')
        # ================

    # ACCEPT BATCH
    def test_07(self):
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
    def test_08(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/make_stage.json"
        data = {'stage': 'sensitive'}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        API_ENDPOINT_4 = self.website + f"/projects/{self.new_project_id}/project.json"
        r4 = requests.get(url=API_ENDPOINT_4, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('MERGE SENSITIVE')
            print('================================')
            pprint(r4.json())

        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/make_stage.json"
        data = {'stage': 'images'}
        r2 = requests.post(url=API_ENDPOINT_2, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['success'], True)

        API_ENDPOINT_4 = self.website + f"/projects/{self.new_project_id}/project.json"
        r4 = requests.get(url=API_ENDPOINT_4, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('MERGE IMAGES')
            print('================================')
            pprint(r4.json())

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
            print('MERGE FINAL')
            print('================================')
            pprint(r4.json())

    # UPDATE SOURCE DICT
    def test_09(self):
        API_ENDPOINT_1 = self.website + f"/{self.source_dict_id}/clone.json"
        r1 = requests.post(url=API_ENDPOINT_1, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        new_dict_id = r1.json()['dictID']

        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/update_source_dict.json"
        data = {'source_dict_id': new_dict_id}
        r2 = requests.post(url=API_ENDPOINT_2, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['success'], True)

        # ================
        # PROJECT STATE
        # ================
        API_ENDPOINT_3 = self.website + f"/projects/{self.new_project_id}/project.json"
        r3 = requests.get(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)
        if self.verbose:
            print('================================')
            print('SOURCE DICT UPDATE')
            print('================================')
            pprint(r3.json())

    # DELETE PROJECT
    def test_10(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/delete.json"
        r1 = requests.post(url=API_ENDPOINT_1, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        self.assertEqual(r1.json()['projectID'], self.new_project_id)

        # ================
        # PROJECT DELETED FORM PROJECT LIST
        # ================
        API_ENDPOINT_2 = self.website + "/projects/list.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        self.assertTrue(self.new_project_id not in r2.json()['projects_active'])
        self.assertTrue(self.new_project_id not in r2.json()['projects_archived'])
        # ================

        API_ENDPOINT_3 = self.website + f"{self.source_dict_id}/destroy.json"
        r3 = requests.post(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r3.json()['success'], True)


if __name__ == '__main__':
    unittest.main()