import sys

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:

    class GenericAlias: ...


if sys.version_info >= (3, 10):
    from types import UnionType
else:

    class UnionType: ...


if sys.version_info >= (3, 11):
    from enum import EnumType
else:
    from enum import EnumMeta as EnumType


# NoneType
if sys.version_info >= (3, 10):
    from types import NoneType
else:

    class NoneType: ...


__all__ = ["GenericAlias", "UnionType", "EnumType", "NoneType"]
