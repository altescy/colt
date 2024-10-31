import typing
from contextlib import suppress
from typing import Any, Callable, Optional, Type, TypeVar, Union

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder, ParamPath
    from colt.context import ColtContext


T = TypeVar("T")


class SkipCallback(Exception): ...


class ColtCallback:
    def on_start(
        self,
        config: Any,
        builder: "ColtBuilder",
        context: "ColtContext",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        del builder, annotation
        return config

    def on_build(
        self,
        path: "ParamPath",
        config: Any,
        builder: "ColtBuilder",
        context: "ColtContext",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        raise SkipCallback


class MultiCallback(ColtCallback):
    def __init__(self, *callbacks: ColtCallback) -> None:
        self.callbacks = callbacks

    def on_start(
        self,
        config: Any,
        builder: "ColtBuilder",
        context: "ColtContext",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        for callback in self.callbacks:
            with suppress(SkipCallback):
                config = callback.on_start(config, builder, context, annotation)
        return config

    def on_build(
        self,
        path: "ParamPath",
        config: Any,
        builder: "ColtBuilder",
        context: "ColtContext",
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Any:
        for callback in self.callbacks:
            with suppress(SkipCallback):
                config = callback.on_build(path, config, builder, context, annotation)
        return config
