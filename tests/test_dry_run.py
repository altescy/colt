import pytest

import colt
from colt import Lazy
from colt.error import ConfigurationError


def test_for_confirming_construction() -> None:
    constructed = False

    class Foo:
        def __init__(self, x: int) -> None:
            nonlocal constructed
            constructed = True
            self.x = x

    config = {"x": 1}
    colt.build(config, Foo)

    assert constructed


def test_dry_run_finish_successfully() -> None:
    constructed = False

    class Foo:
        def __init__(self, x: int) -> None:
            nonlocal constructed
            constructed = True
            self.x = x

    config = {"x": 1}
    colt.dry_run(config, Foo)

    assert not constructed


def test_dry_run_finish_with_error() -> None:
    class Foo:
        def __init__(self, x: int) -> None:
            self.x = x

    config = {"x": "1"}
    with pytest.raises(ConfigurationError):
        colt.dry_run(config, Foo)


def test_dry_run_with_nested_object() -> None:
    class Bar:
        constructed = False

        def __init__(self, y: int) -> None:
            self.y = y
            Bar.constructed = True

    class Foo:
        constructed = False

        def __init__(self, x: int, bar: Bar) -> None:
            self.x = x
            self.bar = bar
            Foo.constructed = True

    config = {"x": 1, "bar": {"y": 2}}
    colt.dry_run(config, Foo)

    assert not Foo.constructed
    assert not Bar.constructed


def test_dry_run_finish_successfully_with_lazy() -> None:
    class Bar:
        constructed = False

        def __init__(self, y: int) -> None:
            self.y = y
            Bar.constructed = True

    class Foo:
        constructed = False

        def __init__(self, x: int, bar: Lazy[Bar]) -> None:
            self.x = x
            self.bar = bar
            Foo.constructed = True

    config = {"x": 1, "bar": {"y": 2}}
    colt.build(config, Foo)

    assert Foo.constructed
    assert not Bar.constructed


def test_dry_run_finish_with_error_with_lazy() -> None:
    class Bar:
        constructed = False

        def __init__(self, y: int) -> None:
            self.y = y
            Bar.constructed = True

    class Foo:
        constructed = False

        def __init__(self, x: int, bar: Lazy[Bar]) -> None:
            self.x = x
            self.bar = bar
            Foo.constructed = True

    config = {"x": 1, "bar": {"y": "2"}}

    with pytest.raises(ConfigurationError):
        colt.build(config, Foo)


def test_dry_run_should_not_raise_error_for_missing_args_with_lazy() -> None:
    class Bar:
        constructed = False

        def __init__(self, y: int) -> None:
            self.y = y
            Bar.constructed = True

    class Foo:
        constructed = False

        def __init__(self, x: int, bar: Lazy[Bar]) -> None:
            self.x = x
            self.bar = bar
            Foo.constructed = True

    config = {"x": 1, "bar": {}}

    foo = colt.build(config, Foo)

    assert isinstance(foo, Foo)
    assert foo.x == 1
    assert isinstance(foo.bar, Lazy)

    bar = foo.bar.construct(y=2)
    assert isinstance(bar, Bar)
    assert bar.y == 2
