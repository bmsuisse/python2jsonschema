import unittest
from python2jsonschema import get_json_schema_for_type
from testtypes import TreeItemConfig


class TestAlot(unittest.TestCase):
    def test_bigtype(self):
        sc = get_json_schema_for_type(TreeItemConfig, error_handling="raise")
        self.assertIsNotNone(sc)
