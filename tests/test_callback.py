import dataclasses
from typing import Any, Callable, Optional, Type, TypeVar, Union

from colt import ColtBuilder, ColtCallback, ColtContext, SkipCallback
from colt.types import ParamPath

T = TypeVar("T")


def test_callback_on_start() -> None:
    @dataclasses.dataclass
    class Foo:
        name: str
        value: int

    class AddName(ColtCallback):
        def on_start(
            self,
            config: Any,
            builder: "ColtBuilder",
            context: "ColtContext",
            annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
        ) -> Any:
            if annotation is Foo and isinstance(config, dict) and "name" not in config:
                return {**config, "name": "foo"}
            raise SkipCallback

    builder = ColtBuilder(callback=AddName())

    config = {"value": 42}
    foo = builder(config, Foo)

    assert isinstance(foo, Foo)
    assert foo.name == "foo"
    assert foo.value == 42


def test_callback_on_build() -> None:
    @dataclasses.dataclass
    class Foo:
        x: int
        y: str

    class AddOne(ColtCallback):
        def on_build(
            self,
            path: "ParamPath",
            config: Any,
            builder: "ColtBuilder",
            context: "ColtContext",
            annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
        ) -> Any:
            del builder, path
            if annotation == int and isinstance(config, int):
                return config + 1
            raise SkipCallback

    builder = ColtBuilder(callback=AddOne())

    config = {"x": 1, "y": "foo"}
    foo = builder(config, Foo)
    assert isinstance(foo, Foo)
    assert foo.x == 2
    assert foo.y == "foo"
