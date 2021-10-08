import importlib
from collections import defaultdict
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from colt.error import ConfigurationError

T = TypeVar("T")
Registry = Dict[Type["Registrable"], Dict[str, Tuple[Type[Any], Optional[str]]]]


class Registrable:
    _registry: ClassVar[Registry] = defaultdict(dict)

    @classmethod
    def register(
        cls,
        name: str,
        constructor: Optional[str] = None,
        exist_ok: bool = False,
    ) -> Callable[[Type[T]], Type[T]]:
        registry = Registrable._registry[cls]

        def decorator(subclass: Type[T]) -> Type[T]:
            if not exist_ok and name in registry:
                raise ValueError(f"type name conflict: {name}")

            if constructor and not hasattr(subclass, constructor):
                raise ValueError(f"constructor {constructor} not found in {subclass}")

            registry[name] = (subclass, constructor)

            return subclass

        return decorator

    @classmethod
    def by_name(cls, name: str) -> Union[Type[T], Callable[..., T]]:
        subclass, constructor = cls.resolve_class_name(name)

        if not constructor:
            return subclass

        return cast(Callable[..., T], getattr(subclass, constructor))

    @classmethod
    def resolve_class_name(cls, name: str) -> Tuple[Type[Any], Optional[str]]:
        registry = Registrable._registry[cls]

        if name in registry:
            subclass, constructor = registry[name]
            return subclass, constructor

        if "." in name:
            submodule, class_name = name.rsplit(".", 1)

            try:
                module = importlib.import_module(submodule)
            except ModuleNotFoundError as e:
                raise ConfigurationError(
                    f"module {submodule} not found ({name})"
                ) from e

            try:
                subclass = getattr(module, class_name)
                constructor = None
                return subclass, constructor
            except AttributeError as e:
                raise ConfigurationError(
                    f"class {class_name} not found in {submodule} ({name})"
                ) from e

        raise ConfigurationError(
            f"{name} is not a registered name for {cls.__name__}. "
        )
