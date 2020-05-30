import typing as tp
from collections import defaultdict


class Registrable:
    _registry: tp.Dict[tp.Type, tp.Dict[str, tp.Type]] = defaultdict(dict)

    @classmethod
    def register(cls, name: str, constructor: str = None):
        registry = Registrable._registry[cls]

        def decorator(T: tp.Type):
            if name in registry:
                raise ValueError(f"type name conflict: {name}")

            if constructor and not hasattr(T, constructor):
                raise ValueError(f"constructor {constructor} not found in {T}")

            setattr(T, "_colt_constructor", constructor)

            registry[name] = T

            return T

        return decorator

    @classmethod
    def get(cls, name: str) -> tp.Type:
        T = Registrable._registry[cls].get(name)

        if T is None:
            raise KeyError(f"type not found: {name}")

        return T
