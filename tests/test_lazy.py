import dataclasses

import colt
from colt import Lazy


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
