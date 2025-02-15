import importlib
import inspect
import pkgutil
import sys
import typing
from collections import abc
from typing import _GenericAlias  # type: ignore[attr-defined]
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
    if b == Any:
        return True
    if a == b == Ellipsis:
        return True

    if isinstance(a, TypeVar):
        if a is b:
            return True
        if a.__bound__ is not None:
            return issubtype(a.__bound__, b)
        if a.__constraints__:
            return all(issubtype(constraint, b) for constraint in a.__constraints__)
        return True
    if isinstance(b, TypeVar):
        if b.__bound__ is not None:
            return issubtype(a, b.__bound__)
        if b.__constraints__:
            return any(issubtype(a, constraint) for constraint in b.__constraints__)
        return True

    a_origin = reveal_origin(a)
    b_origin = reveal_origin(b)
    a_args = typing.get_args(a)
    b_args = typing.get_args(b)

    if a_origin is None or b_origin is None:
        raise ValueError(f"a and b must be type hint, but got {a} and {b}")

    if a_origin == typing.Union:
        return all(issubtype(a_arg, b) for a_arg in a_args)
    if b_origin == typing.Union:
        return any(issubtype(a, b_arg) for b_arg in b_args)

    if a_origin is b_origin or issubclass(a_origin, b_origin):
        if a_args == b_args:
            return True
        if b_args == ():
            return True
        if (
            issubclass(a_origin, tuple)
            and len(a_args) == 2
            and a_args[1] == Ellipsis
            and issubclass(b_origin, Sequence)
            and len(b_args) == 1
        ):
            return issubtype(a_args[0], b_args[0])
        if b_origin is abc.Callable:
            if a_origin is abc.Callable:
                a_callable_args = a_args[0]
                a_callable_return_type = a_args[1]
            else:
                call_method = getattr(a_origin, "__call__", None)
                if call_method is None:
                    return False
                if not b_args:
                    return True
                a_callable_signature = inspect.signature(call_method)
                a_callable_args = tuple(
                    p.annotation
                    for i, (k, p) in enumerate(a_callable_signature.parameters.items())
                    if not (i == 0 and k == "self")
                )
                a_callable_return_type = (
                    a_callable_signature.return_annotation
                    if a_callable_signature.return_annotation != inspect._empty
                    else Any
                )
            b_callable_args = b_args[0]
            b_callable_return_type = b_args[1]
            a_callable_return_type = (
                NoneType if a_callable_return_type is None else a_callable_return_type
            )
            b_callable_return_type = (
                NoneType if b_callable_return_type is None else b_callable_return_type
            )
            if not issubtype(a_callable_return_type, b_callable_return_type):
                return False
            if b_callable_args == Ellipsis:
                return True
            if len(a_callable_args) != len(b_callable_args):
                return False
            return all(
                issubtype(a_arg, b_arg)
                for a_arg, b_arg in zip(a_callable_args, b_callable_args)
            )

        if len(a_args) != len(b_args):
            return False
        if a_args and b_args:
            if all(issubtype(x, y) for x, y in zip(a_args, b_args)):
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
        origin = annotation.__origin__
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


def evaluate_forward_refs(
    ref: ForwardRef, globalns: Dict[str, Any], localns: Dict[str, Any]
) -> Any:
    if sys.version_info >= (3, 12):
        return ref._evaluate(globalns, localns, frozenset(), recursive_guard=frozenset())  # type: ignore[call-arg]
    if sys.version_info >= (3, 9):
        return ref._evaluate(globalns, localns, frozenset())  # type: ignore[call-arg]
    return ref._evaluate(globalns, localns)  # type: ignore[call-arg]
