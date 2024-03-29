import unittest
from typing import TypedDict as typing_TypedDict
import sys

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required, TypedDict
else:
    from typing import NotRequired, Required, TypedDict
from python2jsonschema import get_json_schema_for_type


class TreeTranslation(TypedDict):
    DisplayName: Required[str]
    URL: NotRequired[str]
    HelpUrl: NotRequired[str]


class TreeTranslationTyping(typing_TypedDict):
    DisplayName: Required[str]
    URL: NotRequired[str]
    HelpUrl: NotRequired[str]


class TestTypedDict(unittest.TestCase):
    def test_required(self):
        sc = get_json_schema_for_type(TreeTranslation, error_handling="raise")
        self.assertIsNotNone(sc)
        self.assertEqual(sc["required"], ["DisplayName"])

    def test_required_typing(self):
        sc = get_json_schema_for_type(TreeTranslationTyping, error_handling="raise")
        self.assertIsNotNone(sc)
