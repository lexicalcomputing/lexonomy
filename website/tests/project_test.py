#! /usr/bin/python3.10
import requests
import json
import unittest
import config


class TestQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website

        # LOGIN and get session key
        data = {'email': config.mail,
                'password': config.password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email":r1.json()['email'], 'sessionkey':r1.json()['sessionkey']}

        # generate project id
        r2 = requests.get(url=cls.website + "/projects/suggestid.json",
                          headers=cls.headers, cookies=cls.cookies)
        cls.new_project_id = r2.json()['suggested']

        # get workflow name
        r3 = requests.get(url=cls.website + "/wokflows/list.json",
                          headers=cls.headers, cookies=cls.cookies)
        cls.workflow = r3.json()['workflows'][0]['name']

    # CREATE PROJECT
    def test_1(self):
        API_ENDPOINT_1 = self.website + "/projects/create.json"
        data = {'id': self.new_project_id ,
                'name': 'LCL test project',
                'description': 'This is a testing project',
                'annotators': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']),
                'managers': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk']),
                'ref_corpus': 'test_ref_corpus',
                'source_dict': 'test_source_corpus',
                'workflow': self.workflow,
                'language': 'cs'}
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        self.assertEqual(r1.json()['projectID'], self.new_project_id)

        # test if created correctly
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['description'], 'This is a testing project')
        self.assertEqual(set(r2.json()['managers']) - set(["marek.medved3@gmail.com", "marek.medved@sketchengine.co.uk", "marek.medved@sketchengine.eu"]), set())
        self.assertEqual(set(r2.json()['annotators']) - set(["marek.medved3@gmail.com", "marek.medved@sketchengine.co.uk", "marek.medved@sketchengine.eu"]), set())

        # test if created in user_projects
        API_ENDPOINT_3 = self.website + "/projects/list.json"
        r3 = requests.get(url=API_ENDPOINT_3, headers=self.headers, cookies=self.cookies)
        found = False
        for x in r3.json()['projects_active']:
            if x['id'] == self.new_project_id:
                found = True
        self.assertEqual(found, True)

    # EDIT PROJECT
    def test_2(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/update.json"
        data = {'name': 'LCL test project updated',
                'description': 'This is a testing project updated',
                'annotators': json.dumps(['marek.medved3@gmail.com', 'marek.medved@sketchengine.eu', 'marek.medved@sketchengine.co.uk', 'xmedved1.fi.muni.cz']),
                'managers': json.dumps(['marek.medved@sketchengine.eu']),
                }
        r1 = requests.post(url=API_ENDPOINT_1, data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)

        # test if updated
        API_ENDPOINT_2 = self.website + f"/projects/{self.new_project_id}/project.json"
        r2 = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r2.json()['description'], 'This is a testing project updated')
        self.assertEqual(set(r2.json()['managers']) - set(["marek.medved@sketchengine.eu"]), set())
        self.assertEqual(set(r2.json()['annotators']) - set(['marek.medved3@gmail.com', 'marek.medved@sketchengine.co.uk', 'marek.medved@sketchengine.eu', 'xmedved1.fi.muni.cz']), set())

    # DELETE PROJECT
    def test_3(self):
        API_ENDPOINT_1 = self.website + f"/projects/{self.new_project_id}/archive.json"
        r1 = requests.post(url=API_ENDPOINT_1, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r1.json()['success'], True)
        self.assertEqual(r1.json()['projectID'], self.new_project_id)

        # test if deleted form list
        API_ENDPOINT_2 = self.website + "/projects/list.json"
        r = requests.get(url=API_ENDPOINT_2, headers=self.headers, cookies=self.cookies)
        found = False
        for x in r.json()['projects_archived']:
            if x['id'] == self.new_project_id:
                found = True
        self.assertEqual(found, True)

if __name__ == '__main__':
    unittest.main()