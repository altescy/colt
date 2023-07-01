import datetime
from typing import Any

import colt
from colt import Registrable


def test_strict_mode() -> None:
    class Foo(Registrable):
        ...

    @Foo.register("bar")
    class Bar(Foo):
        def __init__(self, name: str) -> None:
            self.name = name

    class Baz:
        def __init__(self, foo: Foo, extra: Any) -> None:
            self.foo = foo
            self.extra = extra

    config = {
        "foo": {"@type": "bar", "name": "foo"},
        "extra": {
            "@type": "datetime:datetime.fromisoformat",
            "*": ["2023-01-01T00:00:00+09:00"],
        },
    }
    obj = colt.build(config, strict=True)
    assert isinstance(obj, dict)
    assert isinstance(obj["foo"], dict)
    assert isinstance(obj["extra"], dict)

    obj = colt.build(config, Baz, strict=True)
    assert isinstance(obj, Baz)
    assert isinstance(obj.foo, Bar)
    assert isinstance(obj.extra, dict)

    obj = colt.build(config, Baz, strict=False)
    assert isinstance(obj, Baz)
    assert isinstance(obj.foo, Bar)
    assert isinstance(obj.extra, datetime.datetime)
