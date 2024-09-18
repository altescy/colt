from importlib.metadata import version
from typing import Any, Callable, Optional, Type, TypeVar, Union, overload

from colt.builder import ColtBuilder
from colt.default_registry import DefaultRegistry
from colt.lazy import Lazy  # noqa: F401
from colt.registrable import Registrable  # noqa: F401
from colt.utils import import_modules  # noqa: F401

__version__ = version("colt")

T = TypeVar("T")


def register(
    name: str,
    constructor: Optional[str] = None,
    exist_ok: bool = False,
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        DefaultRegistry.register(name, constructor, exist_ok)(cls)
        return cls

    return decorator


@overload
def build(
    config: Any,
    cls: Type[T],
    *,
    typekey: Optional[str] = ...,
    argskey: Optional[str] = ...,
    strict: bool = ...,
) -> T: ...


@overload
def build(
    config: Any,
    cls: Callable[..., T],
    *,
    typekey: Optional[str] = ...,
    argskey: Optional[str] = ...,
    strict: bool = ...,
) -> T: ...


@overload
def build(
    config: Any,
    cls: None = ...,
    *,
    typekey: Optional[str] = ...,
    argskey: Optional[str] = ...,
    strict: bool = ...,
) -> Any: ...


def build(
    config: Any,
    cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    *,
    typekey: Optional[str] = None,
    argskey: Optional[str] = None,
    strict: bool = False,
) -> Union[T, Any]:
    builder = ColtBuilder(typekey, argskey, strict)
    return builder(config, cls)


def dry_run(
    config: Any,
    cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    *,
    typekey: Optional[str] = None,
    argskey: Optional[str] = None,
    strict: bool = False,
) -> None:
    builder = ColtBuilder(typekey, argskey, strict)
    builder.dry_run(config, cls)
