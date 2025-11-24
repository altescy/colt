import copy
import dataclasses
import inspect
import string
import typing
from collections import abc
from enum import Enum
from typing import Any, Callable, Dict, Final, List, Literal, Mapping, Optional, Union

from colt import _constants
from colt._compat import NoneType, UnionType
from colt.lazy import Lazy
from colt.registrable import Registrable
from colt.utils import is_namedtuple

_JSON_SCHEMA: Final = "https://json-schema.org/draft/2020-12/schema"
_SAFE_CHARS: Final = frozenset(string.ascii_letters + string.digits + "_")
_JsonSchemaType = Literal["string", "number", "integer", "boolean", "object", "array", "null"]


def _default(python_type: Any) -> Dict[str, Any]:
    del python_type
    return {
        "type": "object",
        "additionalProperties": True,
        "description": "default schema for unsupported type",
    }


class JsonSchemaGenerator:
    def __init__(
        self,
        *,
        default: Union[Mapping[str, Any], Callable[[Any], Dict[str, Any]]] = _default,
        callback: Optional[Callable[[Optional[str], Dict[str, Any]], Dict[str, Any]]] = None,
        strict: bool = False,
        typekey: str = _constants.DEFAULT_TYPEKEY,
        argskey: str = _constants.DEFAULT_ARGSKEY,
    ) -> None:
        self._default = default
        self._callback = callback
        self._strict = strict
        self._typekey = typekey
        self._argskey = argskey

    def __call__(
        self,
        target: Any,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        definitions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        definitions = copy.deepcopy(definitions) if definitions is not None else {}
        return self._generate(
            target,
            root=True,
            definitions=definitions,
            title=title,
            description=description,
        )

    def _generate(
        self,
        target: Any,
        *,
        root: bool = True,
        definitions: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        extra_properties: Optional[Mapping[str, Any]] = None,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        if definitions is None:
            definitions = {}

        schema: Optional[Dict[str, Any]] = None
        ref_name: Optional[str] = None

        if isinstance(target, str):
            raise ValueError(target)

        if target is Any:
            schema = {}
        elif isinstance(target, type):
            if isinstance(target, type) and issubclass(target, Enum):
                schema = {"enum": [member.value for member in target]}
            elif target in (int, float, str, bool, NoneType):
                schema = {"type": _get_json_type(target)}
            elif target in (list, tuple, set, List, abc.Sequence, abc.MutableSequence, abc.Set):
                schema = {"type": "array"}
            elif target in (dict, Dict, abc.Mapping, abc.MutableMapping):
                schema = {"type": "object"}
            else:
                ref_name = _get_ref_name(target)
                if not root and ref_name in definitions:
                    return {"$ref": f"#/$defs/{ref_name}"}
                if issubclass(target, Registrable):
                    if registry := Registrable._registry[target]:
                        schema = {
                            "anyOf": [
                                self._generate(
                                    getattr(subclass, constructor_name or "__init__"),
                                    root=False,
                                    definitions=definitions | {ref_name: {}},
                                    extra_properties={self._typekey: {"const": name}},
                                    path=path,
                                )
                                for name, (subclass, constructor_name) in registry.items()
                            ]
                        }
                    else:
                        schema = self._generate(
                            target.__init__,
                            root=False,
                            definitions=definitions,
                            path=path,
                        )
                elif dataclasses.is_dataclass(target):
                    fields = [field for field in dataclasses.fields(target) if field.init]
                    schema = {
                        "type": "object",
                        "properties": {
                            field.name: self._generate(
                                field.type,
                                root=False,
                                definitions=definitions,
                                path=_concat_path(path, field.name),
                            )
                            for field in fields
                        },
                        "required": [
                            field.name
                            for field in fields
                            if field.default is field.default_factory is dataclasses.MISSING
                        ],
                    }
                elif is_namedtuple(target):
                    annotations = typing.get_type_hints(target)
                    schema = {
                        "type": "object",
                        "properties": {
                            name: self._generate(
                                annotation,
                                root=False,
                                definitions=definitions,
                                path=_concat_path(path, name),
                            )
                            for name, annotation in typing.get_type_hints(target).items()
                        },
                        "required": [name for name in annotations.keys() if name not in target._field_defaults],
                    }
                elif issubclass(target, dict) and (annotations := typing.get_type_hints(target)):
                    schema = {
                        "type": "object",
                        "properties": {
                            name: self._generate(
                                annotation,
                                root=False,
                                definitions=definitions,
                                path=_concat_path(path, name),
                            )
                            for name, annotation in annotations.items()
                        },
                        "required": [name for name in annotations.keys() if not hasattr(target, name)],
                    }
                elif hasattr(target, "__init__"):
                    schema = self._generate(
                        target.__init__,
                        root=False,
                        definitions=definitions,
                        path=path,
                    )

                if schema is not None:
                    title = title or target.__qualname__
        elif origin := typing.get_origin(target):
            args = typing.get_args(target)
            if origin in (Union, UnionType):  # for Optional and UnionType
                types = [
                    self._generate(
                        t,
                        root=False,
                        definitions=definitions,
                        path=path,
                    )
                    for t in target.__args__
                    if t is not NoneType
                ]  # exclude None
                schema = (
                    {"anyOf": types} if len(types) > 1 else types[0]
                )  # if only one type excluding None, no need to use array
            elif origin in (list, List, abc.Sequence, abc.MutableSequence):  # for List
                schema = {"type": "array"}
                if args:
                    schema["items"] = self._generate(
                        args[0],
                        root=False,
                        definitions=definitions,
                        path=path,
                    )
            elif origin in (dict, Dict, abc.Mapping, abc.MutableMapping):  # for Dict
                schema = {"type": "object"}
                if len(args) == 2 and args[0] is str:
                    schema["additionalProperties"] = self._generate(
                        args[1],
                        root=False,
                        definitions=definitions,
                        path=path,
                    )
            elif origin is Literal:  # for Literal
                schema = {"enum": list(args)}
            elif origin is Lazy:
                schema = self._generate(
                    args[0] if args else Any,
                    root=False,
                    definitions=definitions,
                    path=path,
                )
            else:
                schema = self._generate(
                    origin,
                    root=False,
                    definitions=definitions,
                    path=path,
                )
        elif callable(target):
            sig = inspect.signature(target)
            annotations = typing.get_type_hints(target)
            positional_params = [
                (name, param)
                for pos, (name, param) in enumerate(sig.parameters.items())
                if not (pos == 0 and name in ("self", "target"))
                and param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.VAR_POSITIONAL)
            ]
            keyword_params = [
                (name, param)
                for pos, (name, param) in enumerate(sig.parameters.items())
                if not (pos == 0 and name in ("self", "target"))
                and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
            ]
            var_keyword_param = next(
                (param for param in sig.parameters.values() if param.kind == inspect.Parameter.VAR_KEYWORD),
                None,
            )
            properties = {
                name: self._generate(
                    annotations.get(
                        name,
                        param.annotation if param.annotation is not inspect.Parameter.empty else Any,
                    ),
                    root=False,
                    definitions=definitions,
                    path=_concat_path(path, name),
                )
                for name, param in keyword_params
            }
            if positional_params:
                properties[self._argskey] = {
                    "type": "array",
                    "items": {
                        "anyOf": [
                            self._generate(
                                annotations.get(
                                    name,
                                    param.annotation if param.annotation is not inspect.Parameter.empty else Any,
                                ),
                                root=False,
                                definitions=definitions,
                                path=_concat_path(path, name),
                            )
                            for name, param in positional_params
                        ]
                    },
                }
            schema = {
                "type": "object",
                "properties": properties,
                "required": [name for name, param in keyword_params if param.default is inspect.Parameter.empty],
            }
            if var_keyword_param:
                schema["additionalProperties"] = self._generate(
                    annotations.get(
                        var_keyword_param.name,
                        var_keyword_param.annotation
                        if var_keyword_param.annotation is not inspect.Parameter.empty
                        else Any,
                    ),
                    root=False,
                    definitions=definitions,
                    path=_concat_path(path, var_keyword_param.name),
                )

        if schema is None:
            schema = self._default(target) if callable(self._default) else dict(self._default)

        if title:
            schema["title"] = title
        if description:
            schema["description"] = description
        if extra_properties and schema.get("type") == "object":
            schema.setdefault("properties", {}).update(extra_properties)
            schema.setdefault("required", []).extend(extra_properties.keys())
        if not self._strict:
            schema = {
                "anyOf": [
                    schema,
                    {
                        "type": "object",
                        "properties": {self._typekey: {"type": "string"}},
                        "additionalProperties": True,
                    },
                ]
            }
        if self._callback:
            schema = self._callback(path, schema)

        # Register class schema as reference
        if not root and schema is not None and ref_name is not None:
            definitions[ref_name] = schema
            schema = {"$ref": f"#/$defs/{ref_name}"}

        if root:
            schema = {
                "$schema": _JSON_SCHEMA,
                "$defs": definitions,
                **schema,
            }

        return schema


def _get_ref_name(python_type: type) -> str:
    return f"{_safe_name(python_type.__module__)}__{_safe_name(python_type.__qualname__)}"


def _safe_name(name: str) -> str:
    return "".join(c if c in _SAFE_CHARS else "__" for c in name)


def _concat_path(path: Optional[str], segment: str) -> str:
    if path:
        return f"{path}.{segment}"
    return segment


def _get_json_type(python_type: type) -> _JsonSchemaType:
    if python_type is int:
        return "integer"
    elif python_type is float:
        return "number"
    elif python_type is str:
        return "string"
    elif python_type is bool:
        return "boolean"
    elif python_type is NoneType:
        return "null"
    elif python_type is list:
        return "array"
    return "object"
