import pytest

import colt
from colt.default_registry import DefaultRegistry


class Foo:
    pass


class Bar:
    pass


def test_conflict() -> None:
    colt.register("foobar")(Foo)

    with pytest.raises(ValueError):
        colt.register("foobar")(Bar)


def test_conflict_exist_ok() -> None:
    colt.register("barfoo")(Bar)
    colt.register("barfoo", exist_ok=True)(Foo)

    assert DefaultRegistry.by_name("barfoo") == Foo
