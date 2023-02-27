# python2jsonschema

[![PyPI version](https://badge.fury.io/py/python2jsonschema.svg)](https://badge.fury.io/py/python2jsonschema)

Simple generate a Json Schema for your Python Classes

Does support recursive and complex Data Structures using ForwardRefs:

```python
class Item(TypedDict):
    DisplayName: Required[str]
    Children: List["Union[Item,List[Item]]"]

```

Supports Python 3.9+ (anything below not tested)

## Usage 

There is currently just one method:

```python
from python2jsonschema import get_json_schema_for_type

schema_dict = get_json_schema_for_type(Item, error_handling="raise")

# You might want to save the schema using json.dump or the like

```

## Roadmap / Limitations

Pydantic data models are not yet supported


