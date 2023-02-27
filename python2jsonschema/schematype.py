import dataclasses
from typing import Any, ForwardRef, Literal, Type, Union, get_type_hints, Callable, Any
from uuid import UUID
import sys
import datetime
import types
import logging

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required, get_args, get_origin
else:
    from typing import NotRequired, Required, get_args, get_origin

logger = logging.getLogger(__name__)


def get_json_schema_for_type(
    proptype: Type, *, error_handling: Union[Literal["raise", "warn"], Callable[[Type], Any]] = "warn"
):
    defList: dict[str, dict] = {}
    schema = _get_json_schema_for_type(proptype, defList, rec_level=0, is_root=True, error_handling=error_handling)
    schema["$defs"] = defList
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


class Python2SchemaException(Exception):
    def __init__(self, python_type, *args: object) -> None:
        self.python_type = python_type
        super().__init__(*args)


def _unwrap_requireds(t: Type):
    if get_origin(t) is Required:
        return get_args(t)[0]
    if get_origin(t) is NotRequired:
        return get_args(t)[0]
    return t


def _get_json_schema_for_type(
    proptype: Type,
    defList: dict[str, dict],
    error_handling: Union[Literal["raise", "warn"], Callable[[Type], Any]],
    rec_level: int,
    is_root: bool,
    is_nullable=False,
) -> dict:
    def _fixref(input: dict) -> dict:
        if "type" in input:
            if "$ref" in input["type"]:
                return input["type"]
        return input

    def _may_null(input: dict, is_nullable: bool) -> dict:
        if is_nullable:
            return {"oneOf": [{"type": "null"}, input]}
        return input

    if hasattr(proptype, "__name__") and not is_root and proptype.__name__ in defList:
        return {"$ref": "#/$defs/" + proptype.__name__}
    if hasattr(proptype, "__origin__") and proptype.__origin__ == Literal:
        return {"enum": proptype.__args__}
    if hasattr(proptype, "__origin__") and proptype.__origin__ == tuple:
        return {
            "type": "array",
            "minItems": len(proptype.__args__),
            "maxItems": len(proptype.__args__),
            "additionalItems": False,
            "prefixItems": [
                _get_json_schema_for_type(t, defList, error_handling, rec_level=rec_level + 1, is_root=False)
                for t in proptype.__args__
            ],
        }
    if (sys.version_info >= (3, 10) and isinstance(proptype, types.UnionType)) or (
        hasattr(proptype, "__origin__") and proptype.__origin__ == Union
    ):
        if len(proptype.__args__) == 2 and proptype.__args__[0] == type(None):
            t = _get_json_schema_for_type(
                proptype.__args__[1], defList, error_handling, rec_level=rec_level + 1, is_root=False, is_nullable=True
            )
            return t
        if len(proptype.__args__) == 2 and proptype.__args__[1] == type(None):
            t = _get_json_schema_for_type(
                proptype.__args__[0], defList, error_handling, rec_level=rec_level + 1, is_root=False, is_nullable=True
            )
            return t
        oneOfTypes = [
            _get_json_schema_for_type(
                f, defList, error_handling, rec_level=rec_level + 1, is_root=False, is_nullable=False
            )
            for f in proptype.__args__
        ]
        return {"oneOf": oneOfTypes}
    if proptype == type(None):
        return {"type": "null"}
    if proptype == str:
        return {"type": "string"} if not is_nullable else {"type": ["string", "null"]}

    if proptype == Any:
        return {}  # see https://swagger.io/docs/specification/data-models/data-types/#any
    if proptype == UUID:
        return {
            "type": "string" if not is_nullable else ["string", "null"],
            "format": "uuid",
        }
    if proptype == int:
        return {"type": "integer" if not is_nullable else ["integer", "null"]}
    if proptype == float:
        return {"type": "number" if not is_nullable else ["number", "null"]}
    if proptype == bool:
        return {"type": "boolean" if not is_nullable else ["boolean", "null"]}
    if hasattr(proptype, "__origin__") and proptype.__origin__ == list:
        return {
            "type": "array",
            "items": _get_json_schema_for_type(
                proptype.__args__[0], defList, error_handling, rec_level=rec_level + 1, is_root=False
            ),
        }
    if hasattr(proptype, "__bases__") and len(proptype.__bases__) == 1 and proptype.__bases__[0] == dict:  # TypedDict
        schema_obj = {}
        if hasattr(proptype, "__name__") and not is_root:
            defList[proptype.__name__] = schema_obj
        typehints = get_type_hints(
            proptype, include_extras=False
        )  # As of python 3.11 marking items are required or not is possible, but not supported here yet
        requireds = list(proptype.__required_keys__) if "__required_keys__" in dir(proptype) else []
        props = {
            k: _get_json_schema_for_type(
                _unwrap_requireds(v), defList, error_handling, rec_level=rec_level + 1, is_root=False
            )
            for (k, v) in typehints.items()
        }
        schema_obj["type"] = "object"
        schema_obj["properties"] = props
        if hasattr(proptype, "__name__") and not is_root:
            return _may_null({"$ref": "#/$defs/" + proptype.__name__}, is_nullable)
        else:
            return _may_null({"type": "object", "properties": props, "required": requireds}, is_nullable)
    if dataclasses.is_dataclass(proptype):
        required = [
            f.name
            for f in dataclasses.fields(proptype)
            if f.default == dataclasses.MISSING and f.default_factory == dataclasses.MISSING and f.init == True
        ]
        schema_obj = {"type": "object", "required": required, "additionalProperties": False}
        if not is_root:
            defList[proptype.__name__] = schema_obj  # important to do before recursive call!
        schema_obj["properties"] = {
            f.name: _get_json_schema_for_type(f.type, defList, error_handling, rec_level=rec_level + 1, is_root=False)
            for f in dataclasses.fields(proptype)
        }
        if is_root:
            return schema_obj
        else:
            return _may_null({"$ref": "#/$defs/" + proptype.__name__}, is_nullable)
    if hasattr(proptype, "__origin__") and proptype.__origin__ == dict and len(proptype.__args__) == 2:
        keytype = proptype.__args__[0]
        if keytype != str and keytype != UUID:
            raise NotImplementedError()
        valuetype = proptype.__args__[1]
        return _may_null(
            {
                "type": "object",
                "additionalProperties": _fixref(
                    {
                        "type": _get_json_schema_for_type(
                            valuetype, defList, error_handling, rec_level=rec_level + 1, is_root=False
                        )
                    }
                ),
            },
            is_nullable,
        )
    if isinstance(proptype, ForwardRef):
        arg = proptype.__forward_arg__  # This one is a bit tricky
        if arg.isidentifier():
            return _may_null({"$ref": "#/$defs/" + arg}, is_nullable)
        else:
            typ = eval(arg)
            return _get_json_schema_for_type(typ, defList, error_handling, is_root, is_nullable)
    if proptype == datetime.datetime:
        return {
            "type": "string" if not is_nullable else ["string", "null"],
            "format": "date-time",
        }
    if proptype == datetime.time:
        return {
            "type": "string" if not is_nullable else ["string", "null"],
            "format": "time",
        }
    if proptype == datetime.date:
        return {
            "type": "string" if not is_nullable else ["string", "null"],
            "format": "date",
        }
    if error_handling == "warn":
        logger.warn(f"Cannot generate schema for {proptype}")
    elif error_handling == "raise":
        raise Python2SchemaException(python_type=proptype)
    else:
        error_handling(proptype)
    return {}
