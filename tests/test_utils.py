import sys
from collections import namedtuple
from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)

import pytest

from colt.utils import is_namedtuple, is_typeddict, issubtype, update_field

if sys.version_info >= (3, 9):
    from collections.abc import Iterator
else:
    from typing import Iterator


class Int2Str:
    def __call__(self, x: int) -> str:
        return str(x)


@pytest.mark.parametrize(
    "obj, field, value, expected",
    [
        ({"a": 1}, "a", 2, {"a": 2}),
        ({0: 1}, 0, 2, {0: 2}),
        ({"a": {"b": 1}}, "a.b", 2, {"a": {"b": 2}}),
        ({"a": [1]}, "a.0", 2, {"a": [2]}),
        ({"a": 1}, "b", 2, {"a": 1, "b": 2}),
        ({"a": [1]}, "a.+", 2, {"a": [1, 2]}),
        ({"a": [1, {"b": 1}]}, "a.1.b", 2, {"a": [1, {"b": 2}]}),
        ({"a": {"b": [1]}}, ("a", "b", 0), 2, {"a": {"b": [2]}}),
    ],
)
def test_update_field(
    obj: Union[Dict[Union[int, str], Any], List[Any]],
    field: Union[int, str, List[Union[int, str]]],
    value: Any,
    expected: Union[Dict, List],
) -> None:
    update_field(obj, field, value)
    assert obj == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (int, int, True),
        (int, float, False),
        (List[int], List[int], True),
        (List[int], List[float], False),
        (List[int], List, True),
        (List, List[int], False),
        (List[int], Sequence[int], True),
        (Sequence[int], List[int], False),
        (List[Dict[str, int]], List[Dict[str, int]], True),
        (List[Dict[str, int]], Sequence[Dict[str, int]], True),
        (List[Dict[str, int]], Sequence[Dict[int, int]], False),
        (List[str], Any, True),
        (List[str], List[Any], True),
        (Dict[str, int], Dict[str, Any], True),
        (Tuple[str, int], Tuple[str, int], True),
        (Tuple[str, int], Tuple[str, Any], True),
        (Tuple[str, ...], Tuple[str, ...], True),
        (Tuple[int, ...], Tuple[str, ...], False),
        (Tuple[int, ...], Tuple[Any, ...], True),
        (Tuple[int, ...], Sequence[int], True),
        (int, Optional[int], True),
        (Optional[int], int, False),
        (Union[int, str], Union[int, str, List[str]], True),
        (Union[int, str, List[str]], Union[int, str], False),
        (Iterator[int], Iterator[int], True),
        (Iterator[int], Iterator[str], False),
        (TypeVar("T"), TypeVar("T"), True),
        (TypeVar("T", bound=int), TypeVar("T", bound=Union[int, str]), True),
        (TypeVar("T", bound=Dict), TypeVar("T", bound=Union[int, str]), False),
        (TypeVar("T", bound=Dict[str, str]), Dict[str, Any], True),
        (Dict[str, str], TypeVar("T", bound=Dict[str, Any]), True),
        (int, TypeVar("T", int, str), True),
        (dict, TypeVar("T", int, str), False),
        (TypeVar("T", int, str), Union[int, str], True),
        (TypeVar("T", int, str), str, False),
        (Callable[[int], str], Callable[[int], str], True),
        (Callable[[int], str], Callable[[Union[int, str]], str], True),
        (Callable[[Union[int, str]], str], Callable[[int], str], False),
        (Callable[[Union[int, str]], str], Callable[..., str], True),
        (Int2Str, Callable[[int], str], True),
        (Int2Str, Callable[[str], str], False),
    ],
)
def test_issubtype(a: Any, b: Any, expected: bool) -> None:
    assert issubtype(a, b) == expected


@pytest.mark.parametrize(
    "obj, expected",
    [
        (namedtuple("Point", ["x", "y"]), True),
        (namedtuple("Point", ["x", "y"])(x=1, y=2), True),  # type: ignore[call-arg]
        (NamedTuple("Point", [("x", int), ("y", int)]), True),
        (NamedTuple("Point", [("x", int), ("y", int)])(x=1, y=2), True),  # type: ignore[operator]
        (str, False),
        ("hoge", False),
    ],
)
def test_is_named_tuple(obj: Any, expected: bool) -> None:
    assert is_namedtuple(obj) == expected


@pytest.mark.parametrize(
    "cls, expected",
    [
        (TypedDict("Point", {"x": int, "y": int}), True),  # type: ignore[operator]
        (Dict[str, int], False),
        (str, False),
    ],
)
def test_is_typeddict(cls: Any, expected: bool) -> None:
    assert is_typeddict(cls) == expected
