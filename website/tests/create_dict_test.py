#! /usr/bin/python3.10
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
        self.assertEqual(r.json()["success"], False)

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

        schema_elements = r.json()["elements"]
        schema_elements["entry.my_custom_node"] = {
            "name": "my_custom_node",
            "parent": "entry",
            "min": 0,
            "max": 1,
            "type": "string",
            "values": [],
            "re": ".+",
        }
        schema_elements["entry.placeholder.my_custom_node_delete"] = {
            "name": "my_custom_node_delete",
            "parent": "entry.placeholder",
            "min": 0,
            "max": 1,
            "type": "string",
            "values": [],
            "re": ".+",
        }

        self.assertEqual(r.json()["success"], True)
        self.update_json_schema(
            {
                "elements": schema_elements,
                "root": r.json()["root"],
                "modules": r.json()["modules"],
            }
        )

    # DICT CREATE
    def test_3(self):
        data = {
            "url": "test_create_dict",
            "jsonSchema": json.dumps(self.schema_json),
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
        self.assertEqual(r.json()["success"], True)

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
        self.assertIsNotNone(r.json()["elements"].get("entry.my_custom_node", None))
        self.assertIsNotNone(
            r.json()["removed_nodes"].get(
                "entry.placeholder.my_custom_node_delete", None
            )
        )

        data_update = {
            "id": "structure",
            "url": "test_create_dict",
            "content": json.dumps(
                {
                    "jsonSchema": {
                        "elements": r.json()["elements"],
                        "modules": r.json()["modules"],
                        "root": r.json()["elements"],
                    }
                }
            ),
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
        self.assertIsNotNone(
            r.json()["content"]["elements"].get("entry.my_custom_node", None)
        )

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
        self.assertEqual(r.json()["success"], False)


class SchemaJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_json = {
            "elements": {
                "entry": {
                    "name": "entry",
                    "parent": "",
                    "children": [
                        "entry.pos",
                        "entry.sense",
                    ],
                    "min": 1,
                    "max": 1,
                    "type": "string",
                    "values": [],
                    "re": None,
                },
                "entry.pos": {
                    "name": "pos",
                    "parent": "entry",
                    "min": 0,
                    "max": None,
                    "type": "string",
                    "values": [],
                    "re": ".+",
                },
                "entry.sense": {
                    "name": "sense",
                    "parent": "entry",
                    "children": [
                        "entry.sense.example",
                    ],
                    "min": 0,
                    "max": None,
                    "type": "string",
                    "values": [],
                    "re": None,
                },
                "entry.sense.example": {
                    "name": "example",
                    "parent": "entry.sense",
                    "min": 0,
                    "max": None,
                    "type": "string",
                    "values": [],
                    "re": ".+",
                },
            },
            "root": "entry",
        }
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

    # DICT EXISTS
    def test_1(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], False)

    # DICT CREATE
    def test_2(self):
        data = {
            "url": "test_create_dict",
            "jsonSchema": json.dumps(self.schema_json),
            "title": "test_create_dict",
            "addExamples": "false",
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
    def test_3(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)

    # UPDATE SCHEMA
    def test_4(self):
        data = {
            "id": "structure",
            "url": "test_create_dict",
            "content": json.dumps(
                {
                    "jsonSchema": {
                        "elements": {
                            "entry": {
                                "name": "entry",
                                "parent": "",
                                "children": ["entry.pos"],
                                "min": 1,
                                "max": 1,
                                "type": "string",
                                "values": [],
                                "re": None,
                            },
                            "entry.pos": {
                                "name": "pos",
                                "parent": "entry",
                                "min": 0,
                                "max": None,
                                "type": "string",
                                "values": [],
                                "re": ".+",
                            },
                        },
                        "root": "entry",
                    }
                }
            ),
        }

        r = requests.post(
            url=self.website + "/" + data["url"] + "/dictconfigupdate.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        self.assertEqual(r.json()["success"], True)

    # DICT SCHEMA READ
    def test_5(self):
        data = {"id": "structure", "url": "test_create_dict"}
        r = requests.post(
            url=self.website + "/" + data["url"] + "/configread.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertIsNone(r.json()["content"]["elements"].get("entry.sense", None))

    # DICT REMOVE
    def test_6(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/" + data["url"] + "/destroy.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)

    # DICT EXISTS
    def test_7(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], False)


class SchemaNVH(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_nvh = [
            "entry: * ~.+",
            "  pos: ~.+",
            "  sense: * ~.+",
        ]

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

    # DICT EXISTS
    def test_1(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], False)

    # DICT CREATE
    def test_2(self):
        data = {
            "url": "test_create_dict",
            "nvhSchema": "\n".join(self.schema_nvh),
            "title": "test_create_dict",
            "addExamples": "false",
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
    def test_3(self):
        data = {"url": "test_create_dict"}

        r = requests.post(
            url=self.website + "/exists.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)

    # UPDATE SCHEMA
    def test_4(self):
        new_schema = [
            "entry: * ~.+",
            "  pos: ~.+",
            "  sense: * ~.+",
            "    example: * ~.+",
        ]

        data = {
            "id": "structure",
            "url": "test_create_dict",
            "content": json.dumps({"nvhSchema": "\n".join(new_schema)}),
        }

        r = requests.post(
            url=self.website + "/" + data["url"] + "/dictconfigupdate.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        self.assertEqual(r.json()["success"], True)

    # ADD ENTRY
    def test_5(self):
        entry_example = [
            "entry: test",
            "  pos: N",
            "  sense: test",
            "    example: This is a test",
        ]

        data = {
            "url": "test_create_dict",
            "nvh": "\n".join(entry_example),
        }

        r = requests.post(
            url=self.website + "/" + data["url"] + "/entrycreate.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )

        self.assertEqual(r.json()["success"], True)

    # DICT SCHEMA READ
    def test_6(self):
        data = {"id": "structure", "url": "test_create_dict"}
        r = requests.post(
            url=self.website + "/" + data["url"] + "/configread.json",
            data=data,
            headers=self.headers,
            cookies=self.cookies,
        )
        self.assertIsNotNone(
            r.json()["content"]["elements"].get("entry.sense.example", None)
        )

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
        self.assertEqual(r.json()["success"], False)


if __name__ == "__main__":
    unittest.main()
