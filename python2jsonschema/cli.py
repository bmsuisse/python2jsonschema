import sys
import importlib
import argparse
import json


def cli():
    """Process command line arguments."""
    parser = argparse.ArgumentParser("python2jsonschema")
    parser.add_argument("module_and_type", help="Module and Type in Syntax module.bla:Type")
    parser.add_argument("outfile", type=argparse.FileType("w"))
    args = parser.parse_args()
    module_and_type: str = args.module_and_type
    outfile = args.outfile

    module, type = module_and_type.split(":")
    cls = getattr(importlib.import_module(module), type)

    from python2jsonschema.schematype import get_json_schema_for_type

    schema = get_json_schema_for_type(cls)
    json.dump(schema, outfile, indent=4)
