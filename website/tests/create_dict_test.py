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
        data = {'email': config.admin_mail,
                'password': config.admin_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email":r1.json()['email'], 'sessionkey':r1.json()['sessionkey']}

    # DICT EXISTS
    def test_1(self):
        data = {'url': 'test_create_dict'}
        
        r = requests.post(url=self.website + "/exists.json", data=data, 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], False)

    # DICT CREATE
    def test_2(self):
        data = {'url': 'test_create_dict',
                'schemaKeys': json.dumps(["entry","entry.flag","entry.sense","entry.sense.example"]),
                'title': 'test_create_dict',
                'addExamples': 'false'}
        
        r = requests.post(url=self.website + "/make.json", data=data, 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)
        self.assertEqual(r.json()['url'], data['url'])
        self.assertEqual(r.json()['error'], '')

    # DICT EXISTS
    def test_3(self):
        data = {'url': 'test_create_dict'}
        
        r = requests.post(url=self.website + "/exists.json", data=data, 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)

    # DICT REMOVE
    def test_4(self):
        data = {'url': 'test_create_dict'}
        
        r = requests.post(url=self.website + '/' + data['url'] + "/destroy.json", 
                          data=data, headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], True)

    # DICT EXISTS
    def test_5(self):
        data = {'url': 'test_create_dict'}
        
        r = requests.post(url=self.website + "/exists.json", data=data, 
                          headers=self.headers, cookies=self.cookies)
        self.assertEqual(r.json()['success'], False)

if __name__ == '__main__':
    unittest.main()