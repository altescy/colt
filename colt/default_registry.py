from colt.registrable import Registrable

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


class DefaultRegistry(Registrable):
    """default type store"""


Registrable._registry[DefaultRegistry] = _DEFAULT_TYPES  # pylint:disable=protected-access
