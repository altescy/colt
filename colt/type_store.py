import typing as tp

_DEFAULT_TYPES = {
    "bool": bool,
    "byte": bytes,
    "bytearray": bytearray,
    "memoryview": memoryview,
    "complex": complex,
    "dict": dict,
    "float": float,
    "frozenset": frozenset,
    "int": int,
    "list": list,
    "range": range,
    "set": set,
    "str": str,
    "tuple": tuple,
}


class TypeStore:
    _types: tp.Dict[str, tp.Type] = _DEFAULT_TYPES

    @classmethod
    def add(cls, name: str, T: tp.Type, constructor: str = None) -> None:
        if not isinstance(T, type):
            raise TypeError(f"argument `T` must be a type: {T}")

        if name in cls._types:
            raise ValueError(f"type name conflict: {name}")

        if constructor and not hasattr(T, constructor):
            raise ValueError(f"constructor {constructor} not found in {T}")

        setattr(T, "_colt_constructor", constructor)

        cls._types[name] = T

    @classmethod
    def get(cls, name: str) -> tp.Type:
        T = cls._types.get(name)

        if T is None:
            raise KeyError(f"type not found: {name}")

        return T
