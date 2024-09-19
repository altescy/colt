from typing import Any, Dict, List, Union

import pytest

from colt.utils import update_field


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
