import collections.abc
import importlib
import inspect
import itertools
import pkgutil
import sys
import typing
from contextlib import suppress
from typing import (
    Any,
    Dict,
    ForwardRef,
    Hashable,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    _GenericAlias,  # type: ignore[attr-defined]
    cast,
)

from colt.types import ParamPath

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:

    class GenericAlias:
        __origin__: Any


if sys.version_info >= (3, 10):
    from types import NoneType, UnionType
else:
    NoneType = type(None)

    class UnionType: ...


def import_submodules(package_name: str) -> None:
    """
    original code is here:
    https://github.com/allenai/allennlp/blob/v0.9.0/allennlp/common/util.py
    """
    importlib.invalidate_caches()

    sys.path.append(".")

    # Import at top level
    module = importlib.import_module(package_name)
    path = getattr(module, "__path__", [])
    path_string = "" if not path else path[0]

    for module_finder, name, _ in pkgutil.walk_packages(path):
        if path_string and getattr(module_finder, "path") != path_string:  # noqa: B009
            continue
        subpackage = f"{package_name}.{name}"
        import_submodules(subpackage)


def import_modules(module_names: Iterable[str]) -> None:
    """
    This method import modules recursively.
    You should call this method to register your classes
    if these classes are written on several files.
    """
    for module_name in module_names:
        import_submodules(module_name)


def get_path_name(path: ParamPath) -> str:
    return ".".join(str(x) for x in path)


def update_field(
    obj: Union[Dict[Union[int, str], Any], List[Any]],
    field: Union[int, str, Sequence[Union[int, str]]],
    value: Any,
) -> None:
    path: Sequence[Union[int, str]]
    if isinstance(field, str):
        path = field.split(".")
    elif isinstance(field, int):
        path = (field,)
    else:
        path = field
    if len(path) == 1:
        target_field = path[0]
        if isinstance(obj, dict):
            obj[target_field] = value
        elif isinstance(obj, list):
            if target_field == "+":
                obj.append(value)
            else:
                target_field = int(target_field)
                obj[target_field] = value
        else:
            raise ValueError("obj must be dict or list")
    else:
        target_field = path[0]
        if isinstance(obj, dict):
            update_field(obj[target_field], path[1:], value)
        elif isinstance(obj, list):
            target_field = int(target_field)
            update_field(obj[target_field], path[1:], value)
        else:
            raise ValueError("obj must be dict or list")


def remove_optional(annotation: Any) -> Any:
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin == Union and len(args) == 2 and args[1] == type(None):  # noqa: E721
        return cast(type, args[0])
    return annotation


def reveal_origin(a: Any) -> Optional[Any]:
    if isinstance(a, type) and not isinstance(a, (GenericAlias, _GenericAlias)):
        return a
    return typing.get_origin(a)


def issubtype(a: Any, b: Any) -> bool:
    if a is b:
        return True
    if a == b:
        return True
    if b == Any:
        return True

    if isinstance(a, type) and isinstance(b, type):
        with suppress(TypeError):
            return issubclass(a, b)

    if isinstance(a, TypeVar):
        if a is b:
            return True
        if a.__bound__:
            return issubtype(a.__bound__, b)
        if a.__constraints__:
            return all(issubtype(c, b) for c in a.__constraints__)
        return True
    if isinstance(b, TypeVar):
        if b.__bound__:
            return issubtype(a, b.__bound__)
        if b.__constraints__:
            return any(issubtype(a, c) for c in b.__constraints__)
        return True

    a_origin = reveal_origin(a)
    b_origin = reveal_origin(b)
    a_args = typing.get_args(a)
    b_args = typing.get_args(b)

    if a_args == (Ellipsis,):
        a_args = tuple()
    if b_args == (Ellipsis,):
        b_args = tuple()

    if a_origin is None or b_origin is None:
        raise TypeError(f"Cannot determine origin of {a} or {b}")

    if a_origin in (typing.Union, UnionType):
        return all(issubtype(arg, b) for arg in a_args)
    if b_origin in (typing.Union, UnionType):
        return any(issubtype(a, arg) for arg in b_args)

    if not issubtype(a_origin, b_origin):
        return False

    if a_args == () and b_args == ():
        return True

    if b_origin is collections.abc.Callable:
        if b_args == ():
            return True
        if a_origin is collections.abc.Callable:
            a_call_args = a_args[0]
            a_call_ret = a_args[1]
            if a_call_args is Ellipsis:
                return False
            a_call_required_args = a_call_args
        else:
            call_method = getattr(a_origin, "__call__", None)
            if call_method is None:
                return False
            a_call_signature = inspect.signature(call_method)
            a_call_args = tuple(
                param.annotation
                for i, param in enumerate(a_call_signature.parameters.values())
                if not (i == 0 and param.name == "self")
            )
            a_call_ret = (
                a_call_signature.return_annotation if a_call_signature.return_annotation != inspect._empty else Any
            )
            a_call_required_args = tuple(
                param.annotation
                for i, param in enumerate(a_call_signature.parameters.values())
                if not (i == 0 and param.name == "self") and param.default == inspect._empty
            )
        b_call_args = b_args[0]
        b_call_ret = b_args[1]
        a_call_ret = NoneType if a_call_ret is None else a_call_ret
        b_call_ret = NoneType if b_call_ret is None else b_call_ret
        if not issubtype(a_call_ret, b_call_ret):
            return False
        if b_call_args == Ellipsis:
            return True
        if len(a_call_args) < len(b_call_args):
            return False
        if len(a_call_required_args) > len(b_call_args):
            return False
        return all(issubtype(a_arg, b_arg) for a_arg, b_arg in zip(a_call_args, b_call_args))

    if a_origin == b_origin:
        if b_args == ():
            return True
        if a_args == ():
            return False
        if a_args == b_args:
            return True
        if a_origin is tuple:
            assert issubclass(b_origin, tuple)
            if len(a_args) == 2 and a_args[1] is Ellipsis:
                return len(b_args) == 2 and b_args[1] is Ellipsis and issubtype(a_args[0], b_args[0])
            if len(b_args) == 2 and b_args[1] is Ellipsis:
                return all(issubtype(a_arg, b_args[0]) for a_arg in a_args if a_arg is not Ellipsis)
            return len(a_args) == len(b_args) and all(issubtype(a_arg, b_arg) for a_arg, b_arg in zip(a_args, b_args))
        if a_origin is collections.abc.Callable:
            assert b_origin == collections.abc.Callable
            assert len(a_args) == len(b_args) == 2
            a_params, a_ret = a_args
            b_params, b_ret = b_args
            if not issubtype(a_ret, b_ret):
                return False
            if a_params is Ellipsis:
                return b_params is Ellipsis
            if b_params is Ellipsis:
                return True
            if len(a_params) != len(b_params):
                return False
            return all(issubtype(b_param, a_param) for a_param, b_param in zip(a_params, b_params))
        if len(a_args) != len(b_args):
            return False
        return all(issubtype(a_arg, b_arg) for a_arg, b_arg in zip(a_args, b_args))

    if a_origin is tuple and issubclass(b_origin, collections.abc.Sequence):
        if b_origin is tuple:
            if len(a_args) == 2 and a_args[1] is Ellipsis:
                return len(b_args) == 2 and b_args[1] is Ellipsis and issubtype(a_args[0], b_args[0])
            if len(b_args) == 2 and b_args[1] is Ellipsis:
                return all(issubtype(a_arg, b_args[0]) for a_arg in a_args if a_arg is not Ellipsis)
            return len(a_args) == len(b_args) and all(issubtype(a_arg, b_arg) for a_arg, b_arg in zip(a_args, b_args))
        if b_origin is collections.abc.Sequence:
            if b_args == ():
                return True
            return all(issubtype(a_arg, b_args[0]) for a_arg in a_args if a_arg is not Ellipsis)
        return False

    if a_origin.__module__ in ("builtins", "collections.abc") and b_origin.__module__ in (
        "builtins",
        "collections.abc",
    ):
        # We assume that args of builtin type and  collections.abc generics are directly comparable
        if b_args == ():
            return True
        return all(issubtype(a_args[0], b_args[0]) for a_arg in a_args)

    a_bases = {base for base in getattr(a_origin, "__orig_bases__", ()) if issubtype(base, b_origin)}
    if not a_bases:
        return False

    a_param_maps = {
        param: arg
        for param, arg in itertools.zip_longest(getattr(a_origin, "__parameters__", ()), a_args, fillvalue=Any)
    }

    for a_base in a_bases:
        a_base_params = getattr(a_base, "__parameters__", ())
        if a_base_params:
            a_base = a_base[tuple(a_param_maps.get(param, Any) for param in a_base_params)]
        if issubtype(a_base, b):
            return True

    return False


def is_namedtuple(obj: Any) -> bool:
    if not isinstance(obj, type) and isinstance(obj, object):
        obj = type(obj)
    if not isinstance(obj, type):
        return False
    if not issubclass(obj, tuple):
        return False
    fields = getattr(obj, "_fields", None)
    if not isinstance(fields, tuple):
        return False
    return all(type(name) is str for name in fields)


def is_typeddict(cls: Any) -> bool:
    if not isinstance(cls, type):
        return False
    if not issubclass(cls, dict):
        return False
    return typing.get_type_hints(cls) is not None


def find_typevars(annotation: Any) -> List[TypeVar]:
    if isinstance(annotation, TypeVar):
        return [annotation]
    output: List[TypeVar] = []
    args = typing.get_args(annotation)
    for arg in args:
        output.extend(find_typevars(arg))
    return output


def get_typevar_map(annotation: Any) -> Dict[TypeVar, Any]:
    origin = reveal_origin(annotation)
    if origin is None:
        return {}
    if not hasattr(origin, "__parameters__"):
        return {}
    typevar_map: Dict[TypeVar, Any] = {}
    if origin in (Union, UnionType):
        for arg in typing.get_args(annotation):
            typevar_map.update(get_typevar_map(arg))
        return typevar_map
    for cls in trace_bases(origin):
        if cls is origin:
            continue
        typevar_map.update(get_typevar_map(cls))
    args = typing.get_args(annotation)
    parameters = origin.__parameters__
    typevar_map.update(dict(zip(parameters, args)))
    return typevar_map


def replace_types(annotation: Any, typevar_map: Dict[Any, Any]) -> Any:
    if not typevar_map:
        return annotation
    if isinstance(annotation, Hashable) and annotation in typevar_map:
        return typevar_map[annotation]
    if isinstance(annotation, (GenericAlias, _GenericAlias)):
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        new_args = tuple(replace_types(arg, typevar_map) for arg in args)
        return _GenericAlias(origin, new_args)
    return annotation  # type: ignore[unreachable]


def trace_bases(cls: Type[Any]) -> Iterator[Type[Any]]:
    yield cls
    for base in getattr(cls, "__orig_bases__", getattr(cls, "__bases__", ())):
        yield from trace_bases(base)


def infer_scope(obj: Any) -> Dict[str, Any]:
    cls = type(obj) if not isinstance(obj, type) else obj
    return {
        name: value
        for cls_ in trace_bases(cls)
        for name, value in (
            [(cls_.__module__, sys.modules[cls_.__module__])]
            + list(sys.modules[cls_.__module__].__dict__.items())
            + ([(cls_.__name__, cls_)] if hasattr(cls_, "__name__") else [])
        )
    }


def evaluate_forward_refs(ref: ForwardRef, globalns: Dict[str, Any], localns: Dict[str, Any]) -> Any:
    if sys.version_info >= (3, 12, 4):
        return ref._evaluate(globalns, localns, frozenset(), recursive_guard=frozenset())  # type: ignore[call-arg]
    if sys.version_info >= (3, 9):
        return ref._evaluate(globalns, localns, frozenset())  # type: ignore[call-arg]
    return ref._evaluate(globalns, localns)  # type: ignore[call-arg]
