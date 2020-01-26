import typing as tp

from functools import wraps

from pob.type_store import TypeStore
from pob.build import build


def register(name: str):
    def decorator(T: tp.Type):
        TypeStore.add(name, T)
        return T
    return decorator
