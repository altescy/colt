from typing import Any, Callable, Optional, Type, TypeVar, Union

from colt.builder import ColtBuilder
from colt.default_registry import DefaultRegistry
from colt.registrable import Registrable  # noqa: F401
from colt.utils import import_modules  # noqa: F401
from colt.version import VERSION as __version__  # noqa: F401

T = TypeVar("T")


def register(
    name: str, constructor: Optional[str] = None, exist_ok: bool = False
) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        DefaultRegistry.register(name, constructor, exist_ok)(cls)
        return cls

    return decorator


def build(
    config: Any,
    cls: Optional[Type[T]] = None,
    typekey: Optional[str] = None,
    argskey: Optional[str] = None,
) -> Union[T, Any]:
    builder = ColtBuilder(typekey, argskey)
    return builder(config, cls)
