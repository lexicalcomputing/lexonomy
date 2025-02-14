#!/usr/bin/python3
# coding: utf-8
# Author: Marek Medved, marek.medved@sketchengine.eu, Lexical Computing CZ
import json
import config
import requests
import unittest


class TestSchemaJson2Nvh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ===========================
        # LOGIN TO LEXONOMY
        # ===========================
        cls.headers = {"Content-type": "application/json", "Accept": "text/plain"}
        cls.website = config.website
        data = {"email": config.admin_mail, "password": config.admin_password}
        r1 = requests.post(
            url=cls.website + "/login.json", data=data, headers=cls.headers
        )
        cls.cookies = {
            "email": r1.json()["email"],
            "sessionkey": r1.json()["sessionkey"],
        }
        cls.jsonSchema = {
            "entry": {
                "name": "entry",
                "parent": "",
                "children": [
                    "entry.homograph",
                    "entry.pos",
                    "entry.label",
                    "entry.pronunciation",
                    "entry.form",
                    "entry.sense",
                ],
                "min": 1,
                "max": 1,
                "type": "string",
                "values": [],
                "re": None,
            },
            "entry.homograph": {
                "name": "homograph",
                "parent": "entry",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
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
            "entry.label": {
                "name": "label",
                "parent": "entry",
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.pronunciation": {
                "name": "pronunciation",
                "parent": "entry",
                "children": [
                    "entry.pronunciation.transcription",
                    "entry.pronunciation.label",
                ],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": None,
            },
            "entry.pronunciation.transcription": {
                "name": "transcription",
                "parent": "entry.pronunciation",
                "children": ["entry.pronunciation.transcription.scheme"],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.pronunciation.transcription.scheme": {
                "name": "scheme",
                "parent": "entry.pronunciation.transcription",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.pronunciation.label": {
                "name": "label",
                "parent": "entry.pronunciation",
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form": {
                "name": "form",
                "parent": "entry",
                "children": [
                    "entry.form.tag",
                    "entry.form.label",
                    "entry.form.pronunciation",
                ],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form.tag": {
                "name": "tag",
                "parent": "entry.form",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form.label": {
                "name": "label",
                "parent": "entry.form",
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form.pronunciation": {
                "name": "pronunciation",
                "parent": "entry.form",
                "children": [
                    "entry.form.pronunciation.transcription",
                    "entry.form.pronunciation.label",
                ],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": None,
            },
            "entry.form.pronunciation.transcription": {
                "name": "transcription",
                "parent": "entry.form.pronunciation",
                "children": ["entry.form.pronunciation.transcription.scheme"],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form.pronunciation.transcription.scheme": {
                "name": "scheme",
                "parent": "entry.form.pronunciation.transcription",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.form.pronunciation.label": {
                "name": "label",
                "parent": "entry.form.pronunciation",
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
                    "entry.sense.label",
                    "entry.sense.definition",
                    "entry.sense.example",
                ],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": None,
            },
            "entry.sense.label": {
                "name": "label",
                "parent": "entry.sense",
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.definition": {
                "name": "definition",
                "parent": "entry.sense",
                "children": ["entry.sense.definition.definitionType"],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.definition.definitionType": {
                "name": "definitionType",
                "parent": "entry.sense.definition",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.example": {
                "name": "example",
                "parent": "entry.sense",
                "children": [
                    "entry.sense.example.sourceIdentity",
                    "entry.sense.example.sourceElaboration",
                    "entry.sense.example.soundFile",
                    "entry.sense.example.label",
                ],
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.example.sourceIdentity": {
                "name": "sourceIdentity",
                "parent": "entry.sense.example",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.example.sourceElaboration": {
                "name": "sourceElaboration",
                "parent": "entry.sense.example",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.example.soundFile": {
                "name": "soundFile",
                "parent": "entry.sense.example",
                "min": 0,
                "max": 1,
                "type": "string",
                "values": [],
                "re": ".+",
            },
            "entry.sense.example.label": {
                "name": "label",
                "parent": "entry.sense.example",
                "min": 0,
                "max": None,
                "type": "string",
                "values": [],
                "re": ".+",
            },
        }
        cls.nvhSchema = [
            "entry: string",
            "  homograph: ? string ~.+",
            "  pos: * string ~.+",
            "  label: * string ~.+",
            "  pronunciation: * string",
            "    transcription: * string ~.+",
            "      scheme: ? string ~.+",
            "    label: * string ~.+",
            "  form: * string ~.+",
            "    tag: ? string ~.+",
            "    label: * string ~.+",
            "    pronunciation: * string",
            "      transcription: * string ~.+",
            "        scheme: ? string ~.+",
            "      label: * string ~.+",
            "  sense: * string",
            "    label: * string ~.+",
            "    definition: * string ~.+",
            "      definitionType: ? string ~.+",
            "    example: * string ~.+",
            "      sourceIdentity: ? string ~.+",
            "      sourceElaboration: ? string ~.+",
            "      soundFile: ? string ~.+",
            "      label: * string ~.+",
        ]
        # ===========================

    def test_json2nvh(self):
        r = requests.post(
            url=self.website + "/schema_json_to_nvh.json",
            data={'json_schema': json.dumps(self.jsonSchema)},
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)
        self.assertEqual(r.json()["schema_nvh"], '\n'.join(self.nvhSchema))

    def test_nvh2json(self):
        r = requests.post(
            url=self.website + "/schema_to_json.json",
            data={'schema': '\n'.join(self.nvhSchema)},
            cookies=self.cookies,
        )
        self.assertEqual(r.json()["success"], True)
        self.assertEqual(json.loads(r.json()["schemajson"]), self.jsonSchema)


if __name__ == "__main__":
    unittest.main()
