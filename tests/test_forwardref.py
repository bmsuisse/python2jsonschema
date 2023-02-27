from typing import List, Union
import unittest
import sys

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required, TypedDict
else:
    from typing import NotRequired, Required, TypedDict
from python2jsonschema import get_json_schema_for_type


class Item(TypedDict):
    DisplayName: Required[str]
    URL: NotRequired[str]
    HelpUrl: NotRequired[str]
    Children: List["Union[Item,List[Item]]"]


class TestForwardRef(unittest.TestCase):
    def test_forward(self):
        sc = get_json_schema_for_type(Item, error_handling="raise")
        self.assertIsNotNone(sc)
        self.assertEqual(sorted(sc["required"]), sorted(["DisplayName", "Children"]))
