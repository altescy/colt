import importlib
import pkgutil
import sys
import typing
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union, cast

from colt.types import ParamPath

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:

    class GenericAlias: ...


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
    if isinstance(a, type) and not isinstance(a, GenericAlias):
        return a
    return typing.get_origin(a)


def issubtype(a: Any, b: Any) -> bool:
    if b == Any:
        return True
    if a == b == Ellipsis:
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
