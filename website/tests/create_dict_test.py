#! /usr/bin/python3
import requests
import json
import unittest
import config


class DmLex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_json = {}
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

    @classmethod
    def update_json_schema(cls, schema):
        cls.schema_json = schema

    # DICT EXISTS
    def test_1(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["exists"], False)

    # DmLex schema create
    def test_2(self):
        data = {
            "modules": json.dumps(
                ["core", "xlingual", "values", "linking", "etymology", "annotation"]
            ),
            "xlingual_langs": json.dumps(["en", "fr"]),
            "linking_relations": json.dumps({'meronymy': ["whole", "part"], "synonymy": ["syn"]}),
            "etymology_langs": json.dumps(["oen", "ofr"])
        }

        r = requests.get(
            url=self.website + "/dmlex_schema.json",
            params=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        schema = r.json()["nvhSchema"]
        schema += "  my_custom_node: ? ~.+\n"
        schema += "    my_custom_node_delete: ? ~.+\n"

        self.assertEqual(r.json()["success"], True)
        self.update_json_schema(
            {
                "nvhSchema": schema,
                "root": r.json()["root"],
                "modules": r.json()["modules"],
            }
        )

    # DICT CREATE
    def test_3(self):
        data = {
            "url": "test_create_dict",
            "structure": json.dumps(self.schema_json),
            "title": "test_create_dict",
            "addExamples": "true",
            "dmlex": "true"
        }
        r = requests.post(
            url=self.website + "/make.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)
        self.assertEqual(r.json()["url"], data["url"])
        self.assertEqual(r.json()["error"], "")

    # DICT EXISTS
    def test_4(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["exists"], True)

    # UPDATE SCHEMA
    def test_5(self):
        data = {"modules": json.dumps(["core"])}

        r = requests.get(
            url=self.website + "/test_create_dict/dmlexschemaupdate.json",
            params=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        self.assertEqual(r.json()["success"], True)

        self.assertTrue("my_custom_node_delete" in r.json()["nvhSchema"])

        data_update = {
            "id": "structure",
            "url": "test_create_dict",
            "content": json.dumps({"nvhSchema": r.json()['nvhSchema'], "modules": json.dumps(["core"])}),
        }

        r2 = requests.post(
            url=self.website + "/" + data_update["url"] + "/dictconfigupdate.json",
            data=data_update,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r2.json()["success"], True)

    # DICT SCHEMA READ
    def test_6(self):
        data = {"id": "structure", "url": "test_create_dict"}
        r = requests.post(
            url=self.website + "/" + data["url"] + "/configread.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertTrue("my_custom_node_delete" in r.json()["content"]["nvhSchema"])

    # DICT REMOVE
    def test_7(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/" + data["url"] + "/destroy.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)

    # DICT EXISTS
    def test_8(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["exists"], False)


if __name__ == "__main__":
    unittest.main()
