import typing as tp

from colt.type_store import TypeStore
from colt.builder import ColtBuilder


def register(name: str, constructor: str = None):
    def decorator(T: tp.Type):
        TypeStore.add(name, T, constructor)
        return T
    return decorator

def build(config: tp.Any, typekey: str = None) -> tp.Any:
    builder = ColtBuilder(typekey)
    return builder(config)
