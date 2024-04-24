#! /usr/bin/python3.10
import requests
import json
import unittest
import config
import tempfile
from contextlib import contextmanager


"""
Testing the dictionary configuration, dictionary settings, dictionary access
"""
class AdminTests(unittest.TestCase):
    @contextmanager
    def assertNotRaises(self, exc_type):
        try:
            yield None
        except exc_type:
            raise self.failureException('{} raised'.format(exc_type.__name__))

    @classmethod
    def setUpClass(cls):
        cls.export_filepath = None
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website
        cls.dict_name = 'test_dict_configs_admin'

        # LOGIN and get session key
        data = {'email': config.admin_mail,
                'password': config.admin_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=data, headers=cls.headers)
        cls.cookies = {"email": r1.json()['email'], 'sessionkey': r1.json()['sessionkey']}

    @classmethod
    def update_file_name(cls, value):
        cls.export_filepath = value

    @classmethod
    def update_dict_name(cls, value):
        cls.dict_name = value

    # DICT CREATE
    def test_01(self):
        data = {'url': self.dict_name,
                'schemaKeys': json.dumps(["entry", "entry.flag", "entry.sense", "entry.sense.example"]),
                'title': 'title',
                'addExamples': 'false'}
        r = requests.post(url=self.website + "/make.json", data=data,
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])

    # TEST VALUES NEW DICT
    def test_02(self):
        r = requests.get(url=self.website + "/" + self.dict_name + "/config.json",
                         headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])
        self.assertEqual(r.json()['configs']['ident']['title'], 'title')
        self.assertEqual(r.json()['configs']['ident']['blurb'], 'Yet another Lexonomy dictionary.')
        self.assertEqual(r.json()['configs']['ident'].get('lang'), None)
        self.assertEqual(r.json()['configs']['ident'].get('handle'), None)
        self.assertEqual(r.json()['configs']['dict_settings']['limits']['entries'], 5000)

    # EXPORT CONFIG
    def test_03(self):
        data = {'configs': 'ident,users,publico,structure,formatting,titling,searchability,editing,flagging,autonumber,styles,links,ske,kontext,gapi,dict_settings'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/exportconfigs.json", data=data,
                          headers=self.headers, cookies=self.cookies)

        with self.assertNotRaises(json.decoder.JSONDecodeError):
            json.loads(r.content)
            fp = tempfile.NamedTemporaryFile(delete=False)
            fp.write(r.content)
            self.update_file_name(fp.name)
            fp.close()

    # DICT CONFIG UPDATE
    def test_04(self):
        data = {'id': 'ident',
                'content': json.dumps({"title": "title_after_update", "blurb": "Blurb after update",
                                       "lang": "en", "handle": ""})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictconfigupdate.json" , data=data,
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])

    # DICT ACCESS UPDATE
    def test_05(self):
        data = {'users': json.dumps({"marek.medved@sketchengine.eu": {"canView": True,"canEdit": True,"canConfig": True,"canDownload": True,"canUpload": False},
                                     "xmedved1@fi.muni.cz": {"canView": True,"canEdit": False,"canConfig": False,"canDownload": False,"canUpload": False}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictaccessupdate.json" , data=data,
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])

    # DICT SETTINGS UPDATE
    def test_06(self):
        data = {'configs': json.dumps({"limits": {"entries": 10000}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictsettingsupdate.json" , data=data,
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])

    # TEST VALUES
    def test_07(self):
        r = requests.get(url=self.website + "/" + self.dict_name + "/config.json",
                         headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])
        self.assertEqual(r.json()['configs']['ident']['title'], 'title_after_update')
        self.assertEqual(r.json()['configs']['ident']['blurb'], 'Blurb after update')
        self.assertEqual(r.json()['configs']['ident']['lang'], 'en')
        self.assertEqual(r.json()['configs']['ident']['handle'], '')

        self.assertEqual(r.json()['configs']['dict_settings']['limits']['entries'], 10000)

    # TEST VALUES
    def test_08(self):
        data = {'id': 'users'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/configread.json", data=data,
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])
        self.assertTrue(r.json()['content']['marek.medved@sketchengine.eu']['canConfig'])
        self.assertFalse(r.json()['content']['xmedved1@fi.muni.cz']['canConfig'])

    # IMPORT CONFIG
    def test_09(self):
        f = open(self.export_filepath, 'rb')
        files = {'myfile': (self.export_filepath, f, 'application/json')}
        r = requests.post(self.website + "/" + self.dict_name + "/importconfigs.json", files=files, cookies=self.cookies)
        f.close()

        self.assertTrue(r.json()['success'])

    # TEST VALUES
    def test_10(self):
        r = requests.get(url=self.website + "/" + self.dict_name + "/config.json",
                         headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])
        self.assertEqual(r.json()['configs']['ident']['title'], 'title')
        self.assertEqual(r.json()['configs']['ident']['blurb'], 'Yet another Lexonomy dictionary.')
        self.assertEqual(r.json()['configs']['ident'].get('lang'), None)
        self.assertEqual(r.json()['configs']['ident'].get('handle'), None)
        self.assertEqual(r.json()['configs']['dict_settings']['limits']['entries'], 5000)

    # DICT MOVE
    def test_11(self):
        data = {'url': 'test_dict_configs_admin_moved'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/move.json", data=data,
                         headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])
        self.update_dict_name('test_dict_configs_admin_moved')

    # DICT CLONE
    def test_11(self):
        r = requests.post(url=self.website + "/" + self.dict_name + "/clone.json",
                         headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])

        r2 = requests.post(url=self.website + '/' + r.json()['dictID'] + "/destroy.json",
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r2.json()['success'])

    # DICT REMOVE
    def test_12(self):
        r = requests.post(url=self.website + '/' + self.dict_name + "/destroy.json",
                          headers=self.headers, cookies=self.cookies)
        self.assertTrue(r.json()['success'])


class UserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export_filepath = None
        cls.headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        cls.website = config.website
        cls.dict_name = 'test_dict_configs_user'

        # LOGIN user
        user_data = {'email': config.user_mail,
                     'password': config.user_password}

        r1 = requests.post(url=cls.website + "/login.json",
                           data=user_data, headers=cls.headers)
        cls.user_cookies = {"email": r1.json()['email'], 'sessionkey': r1.json()['sessionkey']}

         # LOGIN admin
        admin_data = {'email': config.admin_mail,
                      'password': config.admin_password}

        r2 = requests.post(url=cls.website + "/login.json",
                           data=admin_data, headers=cls.headers)
        cls.admin_cookies = {"email": r2.json()['email'], 'sessionkey': r2.json()['sessionkey']}

    @classmethod
    def update_file_name(cls, value):
        cls.export_filepath = value

    @classmethod
    def update_dict_name(cls, value):
        cls.dict_name = value

    # DICT CREATE (ADMIN)
    def test_01(self):
        data = {'url': self.dict_name,
                'schemaKeys': json.dumps(["entry", "entry.flag", "entry.sense", "entry.sense.example"]),
                'title': 'title',
                'addExamples': 'false'}
        r = requests.post(url=self.website + "/make.json", data=data,
                          headers=self.headers, cookies=self.admin_cookies)
        self.assertEqual(r.json()['success'], True)

    # DICT ACCESS UPDATE (ADMIN)
    def test_02(self):
        data = {'users': json.dumps({"xmedved1@fi.muni.cz": {"canView": True,"canEdit": False,"canConfig": False,"canDownload": False,"canUpload": False}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictaccessupdate.json" , data=data,
                          headers=self.headers, cookies=self.admin_cookies)
        self.assertEqual(r.json()['success'], True)

    # VERIFY DATA (ADMIN)
    def test_03(self):
        data = {'id': 'users'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/configread.json", data=data,
                          headers=self.headers, cookies=self.admin_cookies)
        self.assertEqual(r.json()['success'], True)
        self.assertEqual(r.json()['content']['xmedved1@fi.muni.cz']['canView'], True)
        self.assertEqual(r.json()['content']['xmedved1@fi.muni.cz']['canEdit'], False)
        self.assertEqual(r.json()['content']['xmedved1@fi.muni.cz']['canConfig'], False)
        self.assertEqual(r.json()['content']['xmedved1@fi.muni.cz']['canDownload'], False)
        self.assertEqual(r.json()['content']['xmedved1@fi.muni.cz']['canUpload'], False)

    # DICT ACCESS UPDATE FAIL (USER)
    def test_04(self):
        data = {'users': json.dumps({"xmedved1@fi.muni.cz": {"canView": True,"canEdit": True,"canConfig": True,"canDownload": True,"canUpload": True}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictaccessupdate.json" , data=data,
                          headers=self.headers, cookies=self.user_cookies)
        self.assertFalse('success' in r.json())

    # DICT SETTINGS UPDATE FAIL (USER)
    def test_05(self):
        data = {'configs': json.dumps({"limits": {"entries": 10000000}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictsettingsupdate.json" , data=data,
                          headers=self.headers, cookies=self.user_cookies)
        # TODO redirect fix and check result

    # DICT MOVE FAIL (USER)
    def test_06(self):
        data = {'url': 'test_dict_configs_moved'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/move.json", data=data,
                         headers=self.headers, cookies=self.user_cookies)
        self.assertFalse('success' in r.json())

    # DICT CLONE PASS (USER)
    def test_07(self):
        r = requests.post(url=self.website + "/" + self.dict_name + "/clone.json",
                         headers=self.headers, cookies=self.user_cookies)
        self.assertTrue(r.json()['success'])

        r2 = requests.post(url=self.website + '/' + r.json()['dictID'] + "/destroy.json",
                          headers=self.headers, cookies=self.user_cookies)
        self.assertTrue(r2.json()['success'])

    # DICT REMOVE FAIL (USER)
    def test_08(self):
        r = requests.post(url=self.website + '/' + self.dict_name + "/destroy.json",
                          headers=self.headers, cookies=self.user_cookies)
        self.assertFalse('success' in r.json())

    # DICT ACCESS UPDATE (ADMIN) - user can config now
    def test_09(self):
        data = {'users': json.dumps({"xmedved1@fi.muni.cz": {"canView": True,"canEdit": False,"canConfig": True,"canDownload": False,"canUpload": False}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictaccessupdate.json" , data=data,
                          headers=self.headers, cookies=self.admin_cookies)
        self.assertEqual(r.json()['success'], True)

    # DICT ACCESS UPDATE PASS (USER)
    def test_10(self):
        data = {'users': json.dumps({"xmedved1@fi.muni.cz": {"canView": True,"canEdit": True,"canConfig": True,"canDownload": True,"canUpload": True}})}
        r = requests.post(url=self.website + "/" + self.dict_name + "/dictaccessupdate.json" , data=data,
                          headers=self.headers, cookies=self.user_cookies)
        self.assertTrue(r.json()['success'])

    # DICT MOVE PASS (USER)
    def test_11(self):
        data = {'url': 'test_dict_configs_user_moved'}
        r = requests.post(url=self.website + "/" + self.dict_name + "/move.json", data=data,
                         headers=self.headers, cookies=self.user_cookies)
        self.assertTrue(r.json()['success'])
        self.update_dict_name('test_dict_configs_user_moved')

    # DICT REMOVE (USER)
    def test_12(self):
        r = requests.post(url=self.website + '/' + self.dict_name + "/destroy.json",
                          headers=self.headers, cookies=self.user_cookies)
        self.assertTrue(r.json()['success'])


if __name__ == '__main__':
    unittest.main()