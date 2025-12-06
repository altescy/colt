import copy
import dataclasses
import inspect
import json
import string
import typing
from abc import ABCMeta
from collections import abc, defaultdict
from enum import Enum
from typing import Any, Callable, Dict, Final, List, Literal, Mapping, Optional, Tuple, Union

from colt import _constants
from colt._compat import NoneType, UnionType
from colt.lazy import Lazy
from colt.registrable import Registrable
from colt.types import ParamPath
from colt.utils import is_namedtuple

_JSON_SCHEMA: Final = "https://json-schema.org/draft/2020-12/schema"
_SAFE_CHARS: Final = frozenset(string.ascii_letters + string.digits + "_")
_JsonSchemaType = Literal["string", "number", "integer", "boolean", "object", "array", "null"]


@dataclasses.dataclass(frozen=True)
class JsonSchemaContext:
    target: Any
    root: bool = True
    definitions: Optional[Dict[str, Any]] = None
    title: Optional[str] = None
    description: Optional[str] = None
    extra_properties: Optional[Mapping[str, Any]] = None
    path: ParamPath = ()


def _default(context: JsonSchemaContext) -> Dict[str, Any]:
    del context
    return {
        "type": "object",
        "additionalProperties": True,
        "description": "default schema for unsupported type",
    }


class JsonSchemaGenerator:
    def __init__(
        self,
        *,
        default: Union[Mapping[str, Any], Callable[[JsonSchemaContext], Dict[str, Any]]] = _default,
        callback: Optional[Callable[[Dict[str, Any], JsonSchemaContext], Dict[str, Any]]] = None,
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
        schema = self._generate(
            target,
            root=True,
            definitions=definitions,
            title=title,
            description=description,
        )
        return _normalize_schema(schema)

    def _get_any_colt_schema(self, description: Optional[str] = None) -> Dict[str, Any]:
        assert not self._strict
        return {
            "type": "object",
            "properties": {self._typekey: {"type": "string"}},
            "additionalProperties": True,
            "required": [self._typekey],
            **({"description": description} if description else {}),
        }

    def _generate(
        self,
        target: Any,
        *,
        root: bool = True,
        definitions: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        extra_properties: Optional[Mapping[str, Any]] = None,
        path: ParamPath = (),
    ) -> Dict[str, Any]:
        if definitions is None:
            definitions = {}

        schema: Optional[Dict[str, Any]] = None
        ref_name: Optional[str] = None

        if isinstance(target, str):
            if self._strict:
                raise ValueError(target)
            schema = self._get_any_colt_schema(description or f"dynamic type '{target}'")
        elif target is Any:
            if self._strict:
                raise ValueError("typing.Any is not supported in strict mode")
            schema = self._get_any_colt_schema(description or "any type")
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
                        definitions.update({ref_name: {}})  # prevent recursion
                        subclasses = defaultdict(list)
                        for name, (subclass, constructor_name) in registry.items():
                            subclasses[(subclass, constructor_name)].append(name)
                        subschemas = {
                            _get_ref_name(subclass): self._generate(
                                getattr(subclass, constructor_name or "__init__"),
                                root=False,
                                definitions=definitions,
                                extra_properties={self._typekey: _make_any_of(*({"const": name} for name in names))},
                                path=path,
                                title=subclass.__qualname__,
                            )
                            for (subclass, constructor_name), names in subclasses.items()
                        }
                        schema = _make_any_of(*({"$ref": f"#/$defs/{ref_name}"} for ref_name in subschemas.keys()))
                        definitions.update(subschemas)
                    else:
                        schema = self._generate(
                            target.__init__,
                            root=False,
                            definitions=definitions,
                            path=path,
                            extra_properties=extra_properties,
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
                elif isinstance(target, ABCMeta):
                    if self._strict:
                        description = description or "[WARNING] abstract base classes are not supported in strict mode"
                    else:
                        schema = self._get_any_colt_schema(
                            description or f"abstract base class {target.__module__}.{target.__qualname__}"
                        )
                elif getattr(target, "_is_protocol", False):
                    if self._strict:
                        description = description or "[WARNING] protocol types are not supported in strict mode"
                    else:
                        schema = self._generate(
                            description or f"protocol type {target.__module__}.{target.__qualname__}"
                        )
                elif hasattr(target, "__init__"):
                    schema = self._generate(
                        target.__init__,
                        root=False,
                        definitions=definitions,
                        path=path,
                    )

                if not self._strict and (subclasses := target.__subclasses__()):
                    schema = _make_any_of(
                        *((schema,) if schema is not None else ()),
                        *(
                            self._generate(
                                subclass,
                                root=False,
                                definitions=definitions,
                                extra_properties=None
                                if isinstance(subclass, ABCMeta)
                                else {self._typekey: {"const": f"{subclass.__module__}.{subclass.__qualname__}"}},
                                path=path,
                            )
                            for subclass in subclasses
                        ),
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
                schema = _make_any_of(*types)
            elif origin in (list, List, abc.Sequence, abc.MutableSequence):  # for List
                schema = {"type": "array"}
                if args:
                    schema["items"] = self._generate(
                        args[0],
                        root=False,
                        definitions=definitions,
                        path=_concat_path(path, "<index>"),
                    )
            elif origin in (tuple, Tuple):  # for Tuple
                schema = {"type": "array"}
                if args:
                    if len(args) == 2 and args[1] is Ellipsis:
                        schema["items"] = self._generate(
                            args[0],
                            root=False,
                            definitions=definitions,
                            path=_concat_path(path, "<index>"),
                        )
                    else:
                        schema["prefixItems"] = [
                            self._generate(
                                arg,
                                root=False,
                                definitions=definitions,
                                path=_concat_path(path, idx),
                            )
                            for idx, arg in enumerate(args)
                        ]
            elif origin in (dict, Dict, abc.Mapping, abc.MutableMapping):  # for Dict
                schema = {"type": "object"}
                if len(args) == 2 and args[0] is str:
                    schema["additionalProperties"] = self._generate(
                        args[1],
                        root=False,
                        definitions=definitions,
                        path=_concat_path(path, "<key>"),
                    )
            elif origin in (Callable, abc.Callable):  # for Callable
                if self._strict:
                    schema = {"type": "object"}
                    description = "[WARNING] callable types are not supported in strict mode"
                else:
                    schema = self._get_any_colt_schema(description or "callable type")
                    description = description or f"callable type {target}"
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
            sig: Optional[inspect.Signature] = None
            try:
                sig = inspect.signature(target)
            except ValueError:
                pass

            if sig is not None:
                annotations = typing.get_type_hints(target)
                positional_params = [
                    (name, param)
                    for pos, (name, param) in enumerate(sig.parameters.items())
                    if not (pos == 0 and name in ("self", "target")) and param.kind == inspect.Parameter.POSITIONAL_ONLY
                ]
                var_positional_param = next(
                    (param for param in sig.parameters.values() if param.kind == inspect.Parameter.VAR_POSITIONAL),
                    None,
                )
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
                if positional_params or var_positional_param:
                    prefix_items = [
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
                    items = (
                        self._generate(
                            annotations.get(
                                var_positional_param.name,
                                var_positional_param.annotation
                                if var_positional_param
                                and var_positional_param.annotation is not inspect.Parameter.empty
                                else Any,
                            ),
                            root=False,
                            definitions=definitions,
                            path=_concat_path(path, var_positional_param.name) if var_positional_param else path,
                        )
                        if var_positional_param
                        else False
                    )
                    properties[self._argskey] = {
                        "type": "array",
                        **({"prefixItems": prefix_items} if prefix_items else {}),
                        **({"items": items} if items is not False else {}),
                    }
                schema = {
                    "type": "object",
                    "properties": properties,
                    "required": [name for name, param in keyword_params if param.default is inspect.Parameter.empty],
                    "additionalProperties": False,
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

        context = JsonSchemaContext(
            target=target,
            root=root,
            definitions=definitions,
            title=title,
            description=description,
            extra_properties=extra_properties,
            path=path,
        )

        if schema is None:
            schema = self._default(context) if callable(self._default) else dict(self._default)

        if title:
            schema["title"] = title
        if description:
            schema["description"] = description
        if extra_properties and schema.get("type") == "object":
            schema.setdefault("properties", {}).update(extra_properties)
            schema["required"] = sorted(set(schema.get("required", [])) | set(extra_properties.keys()))

        # Register class schema as reference
        if not root and schema is not None and ref_name is not None:
            definitions[ref_name] = schema
            schema = {"$ref": f"#/$defs/{ref_name}"}

        if self._callback:
            schema = self._callback(schema, context)

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


def _concat_path(path: ParamPath, segment: Union[int, str]) -> ParamPath:
    return path + (segment,)


def _flatten_any_of(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    if subschemas := schema.get("anyOf"):
        result: list[Dict[str, Any]] = []
        for subschema in subschemas:
            result.extend(_flatten_any_of(subschema))
        return result
    return [schema]


def _make_any_of(*schemas: Dict[str, Any]) -> Dict[str, Any]:
    if len(schemas) == 1:
        return schemas[0]
    flattened_schemas = []
    for schema in schemas:
        if not any(_is_equal_schema(schema, existing) for existing in flattened_schemas):
            flattened_schemas.extend(_flatten_any_of(schema))
    return {"anyOf": flattened_schemas}


def _is_equal_schema(schema1: Dict[str, Any], schema2: Dict[str, Any]) -> bool:
    """Check if two JSON schemas are equal, ignoring title and description.

    Note: Given schemas are assumed to be normalized.
    """

    ignore_keys = {"title", "description"}

    schema1_keys = set(schema1.keys()) - ignore_keys
    schema2_keys = set(schema2.keys()) - ignore_keys
    if schema1_keys != schema2_keys:
        return False

    for key in schema1_keys:
        value1 = schema1[key]
        value2 = schema2[key]
        if key == "anyOf":
            if len(value1) != len(value2):
                return False
            for subvalue1 in value1:
                if not any(_is_equal_schema(subvalue1, subvalue2) for subvalue2 in value2):
                    return False
        elif isinstance(value1, dict) and isinstance(value2, dict):
            if not _is_equal_schema(value1, value2):
                return False
        elif value1 != value2:
            return False

    return True


def _normalize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    def _dfs(o: Any) -> Any:
        if isinstance(o, dict):
            if set(o.keys()) == {"anyOf"}:
                subschemas = _flatten_any_of(o)
                # Remove duplicate schemas
                unique_subschemas = []
                for subschema in subschemas:
                    subschema = _dfs(subschema)
                    if not any(_is_equal_schema(subschema, existing) for existing in unique_subschemas):
                        unique_subschemas.append(subschema)
                # Sort schemas to ensure consistent order
                unique_subschemas.sort(key=lambda s: json.dumps(s, sort_keys=True))
                o = {"anyOf": unique_subschemas}
            elif o.get("type") == "object":
                if isinstance(o.get("properties"), dict):
                    o["properties"] = {key: _dfs(value) for key, value in o["properties"].items()}
                if isinstance(o.get("additionalProperties"), dict):
                    o["additionalProperties"] = _dfs(o["additionalProperties"])
                if isinstance(o.get("required"), list):
                    o["required"] = sorted(set(o["required"]))
                if isinstance(o.get("$defs"), dict):
                    o["$defs"] = {key: _dfs(value) for key, value in o["$defs"].items()}
            else:
                o = {key: _dfs(value) for key, value in o.items()}
        elif isinstance(o, list):
            o = [_dfs(item) for item in o]
        return o

    return _dfs(schema)


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
