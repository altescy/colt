import typing
from contextlib import suppress
from typing import Any, Callable, Optional, Type, TypeVar, Union

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder, ParamPath


T = TypeVar("T")


class SkipCallback(Exception): ...


class ColtCallback:
    def on_start(
        self,
        builder: "ColtBuilder",
        config: Any,
        cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        del builder, cls
        return config

    def on_build(
        self,
        builder: "ColtBuilder",
        config: Any,
        path: "ParamPath",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        raise SkipCallback


class MultiCallback(ColtCallback):
    def __init__(self, *callbacks: ColtCallback) -> None:
        self.callbacks = callbacks

    def on_start(
        self,
        builder: "ColtBuilder",
        config: Any,
        cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        for callback in self.callbacks:
            with suppress(SkipCallback):
                config = callback.on_start(builder, config, cls)
        return config

    def on_build(
        self,
        builder: "ColtBuilder",
        config: Any,
        path: "ParamPath",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        for callback in self.callbacks:
            with suppress(SkipCallback):
                config = callback.on_build(builder, config, path, annotation)
        return config
