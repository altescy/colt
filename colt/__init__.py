import typing as tp

from colt.registrable import Registrable
from colt.default_registry import DefaultRegistry
from colt.builder import ColtBuilder
from colt.utils import import_modules
from colt.version import VERSION as __version__


def register(name: str, constructor: str = None, exist_ok: bool = False):
    def decorator(T: tp.Type):
        DefaultRegistry.register(name, constructor, exist_ok)(T)
        return T

    return decorator


def build(config: tp.Any,
          cls: tp.Type = None,
          typekey: str = None,
          argskey: str = None) -> tp.Any:
    builder = ColtBuilder(typekey, argskey)
    return builder(config, cls)
