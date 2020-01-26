import typing as tp


_DEFAULT_TYPES = {
    "bool": bool,
    "dict": dict,
    "float": float,
    "int": int,
    "list": list,
    "set": set,
    "str": str,
}


class TypeStore:
    _types: tp.Dict[str, tp.Type] = _DEFAULT_TYPES

    @classmethod
    def add(cls, name: str, T: tp.Type) -> None:
        if not isinstance(T, type):
            raise TypeError(f"argument `T` must be a type: {T}")

        if name in cls._types:
            raise ValueError(f"type name conflict: {name}")

        cls._types[name] = T

    @classmethod
    def get(cls, name: str) -> tp.Type:
        T = cls._types.get(name)

        if T is None:
            raise KeyError(f"type not found: {name}")

        return T
