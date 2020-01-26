import typing as tp

from functools import wraps

from pob.type_store import TypeStore
from pob.builder import ColtBuilder


def register(name: str):
    def decorator(T: tp.Type):
        TypeStore.add(name, T)
        return T
    return decorator

def build(config: tp.Any, typekey: str = None) -> tp.Any:
    builder = ColtBuilder(typekey)
    return builder(config)
