import typing as tp

from colt.type_store import TypeStore
from colt.builder import ColtBuilder
from colt.utils import import_modules
from colt.version import VERSION as __version__


def register(name: str, constructor: str = None):
    def decorator(T: tp.Type):
        TypeStore.add(name, T, constructor)
        return T

    return decorator


def build(config: tp.Any, typekey: str = None, argskey: str = None) -> tp.Any:
    builder = ColtBuilder(typekey, argskey)
    return builder(config)
