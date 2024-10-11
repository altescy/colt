from importlib.metadata import version
from typing import Any, Callable, Optional, Sequence, Type, TypeVar, Union, overload

from colt.builder import ColtBuilder
from colt.callback import ColtCallback, SkipCallback  # noqa: F401
from colt.context import ColtContext  # noqa: F401
from colt.default_registry import DefaultRegistry
from colt.error import ConfigurationError  # noqa: F401
from colt.lazy import Lazy  # noqa: F401
from colt.placeholder import Placeholder  # noqa: F401
from colt.registrable import Registrable  # noqa: F401
from colt.utils import import_modules  # noqa: F401

__version__ = version("colt")
__all__ = [
    "Lazy",
    "Registrable",
    "ConfigurationError",
    "DefaultRegistry",
    "import_modules",
    "register",
    "build",
    "dry_run",
]

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
    callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = ...,
) -> T: ...


@overload
def build(
    config: Any,
    cls: Callable[..., T],
    *,
    typekey: Optional[str] = ...,
    argskey: Optional[str] = ...,
    strict: bool = ...,
    callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = ...,
) -> T: ...


@overload
def build(
    config: Any,
    cls: None = ...,
    *,
    typekey: Optional[str] = ...,
    argskey: Optional[str] = ...,
    strict: bool = ...,
    callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = ...,
) -> Any: ...


def build(
    config: Any,
    cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    *,
    typekey: Optional[str] = None,
    argskey: Optional[str] = None,
    strict: bool = False,
    callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = None,
) -> Union[T, Any]:
    builder = ColtBuilder(typekey, argskey, strict, callback)
    return builder(config, cls)


def dry_run(
    config: Any,
    cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    *,
    typekey: Optional[str] = None,
    argskey: Optional[str] = None,
    strict: bool = False,
    callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = None,
) -> None:
    builder = ColtBuilder(typekey, argskey, strict, callback)
    builder.dry_run(config, cls)
