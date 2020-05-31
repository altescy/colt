import typing as tp
from collections import defaultdict

T = tp.TypeVar("T", bound="Registrable")


class Registrable:
    _registry: tp.Dict[tp.Type, tp.Dict[str, tp.Type]] = defaultdict(dict)

    @classmethod
    def register(cls: tp.Type[T],
                 name: str,
                 constructor: str = None,
                 exist_ok: bool = False):
        registry = Registrable._registry[cls]

        def decorator(subclass: tp.Type[T]):
            if not exist_ok and name in registry:
                raise ValueError(f"type name conflict: {name}")

            if constructor and not hasattr(subclass, constructor):
                raise ValueError(
                    f"constructor {constructor} not found in {subclass}")

            setattr(subclass, "_colt_constructor", constructor)

            registry[name] = subclass

            return subclass

        return decorator

    @classmethod
    def by_name(cls: tp.Type[T], name: str) -> tp.Type[T]:
        subclass = Registrable._registry[cls].get(name)

        if subclass is None:
            raise KeyError(f"type not found: {name}")

        return subclass
