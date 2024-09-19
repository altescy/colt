import dataclasses

import pytest

import colt
from colt import ConfigurationError, Lazy


def test_lazy() -> None:
    @dataclasses.dataclass
    class Foo:
        x: str
        y: int

    @dataclasses.dataclass
    class Bar:
        foo: Lazy[Foo]

    bar = colt.build({"foo": {"x": "hello"}}, Bar)

    assert isinstance(bar, Bar)
    assert isinstance(bar.foo, Lazy)

    foo = bar.foo.construct(y=10)
    assert isinstance(foo, Foo)
    assert foo.x == "hello"
    assert foo.y == 10


def test_lazy_update() -> None:
    @dataclasses.dataclass
    class Foo:
        name: str

    @dataclasses.dataclass
    class Bar:
        foo: Lazy[Foo]

    bar = colt.build({"foo": {"name": "foo"}}, Bar)

    assert isinstance(bar, Bar)
    assert isinstance(bar.foo, Lazy)

    bar.foo.update(name="bar")
    assert bar.foo.config == {"name": "bar"}

    bar.foo.update({"name": "baz"})
    assert bar.foo.config == {"name": "baz"}

    with pytest.raises(ConfigurationError):
        bar.foo.update(name=123)
