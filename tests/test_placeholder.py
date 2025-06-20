import dataclasses
from typing import Any, Set, Union

import pytest

import colt
from colt import ConfigurationError, Placeholder


def test_build_with_placeholder_successfully() -> None:
    @dataclasses.dataclass
    class Foo:
        a: int

    @dataclasses.dataclass
    class Bar:
        foo: Foo
        tags: Set[str]

    config = {"foo": Placeholder(Foo), "tags": Placeholder(Set[str])}
    colt.dry_run(config, Bar)


def test_build_with_placeholder_with_error() -> None:
    @dataclasses.dataclass
    class Foo:
        a: int

    @dataclasses.dataclass
    class Bar:
        foo: Foo
        tags: Set[str]

    config = {"foo": Placeholder(Foo), "tags": Placeholder(Set[int])}

    with pytest.raises(ConfigurationError):
        colt.dry_run(config, Bar)


def test_placeholder_without_annotation() -> None:
    class Foo:
        def __init__(self, value) -> None:  # type: ignore[no-untyped-def]
            self.value = value

    colt.dry_run({"foo": Placeholder(Foo)}, Foo)


@pytest.mark.parametrize(
    "placeholder, annotation, expected",
    [
        (int, int, True),
        (int, str, False),
        (int, Union[int, str], True),
        (int, Union[str, float], False),
    ],
)
def test_placeholder_match_type_hint(placeholder: Any, annotation: Any, expected: bool) -> None:
    assert Placeholder(placeholder).match_type_hint(annotation) == expected
