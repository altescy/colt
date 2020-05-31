#pylint: disable=too-many-return-statements,too-many-branches
import typing as tp

import copy

from colt.error import ConfigurationError
from colt.default_registry import DefaultRegistry
from colt.registrable import Registrable


class ColtBuilder:
    _DEFAULT_TYPEKEY = "@type"
    _DEFAULT_ARGSKEY = "*"

    def __init__(self, typekey: str = None, argskey: str = None) -> None:
        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY

    def __call__(self, config: tp.Any, cls: tp.Type = None) -> tp.Any:
        return self._build(config, cls)

    @staticmethod
    def _remove_optional(annotation: type):
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())
        if origin == tp.Union and len(args) == 2 and args[1] == type(None):
            return args[0]
        return annotation

    @staticmethod
    def _get_constructor_by_name(name: str, annotation: tp.Type = None):
        if annotation and issubclass(annotation, Registrable):
            constructor = annotation.by_name(name)
        else:
            constructor = DefaultRegistry.by_name(name)

        if constructor is None:
            raise ConfigurationError(f"type not found error: {name}")

        return constructor

    def _construct_with_args(self, constructor: tp.Callable,
                             config: tp.Dict[str, tp.Any]) -> tp.Any:
        if not config:
            return constructor()

        args_config = config.pop(self._argskey, [])
        if not isinstance(args_config, (list, tuple)):
            raise ConfigurationError("args must be a list or tuple")
        args = [self._build(val) for val in args_config]

        if isinstance(constructor, type):
            type_hints = tp.get_type_hints(getattr(constructor, "__init__"))
        else:
            type_hints = tp.get_type_hints(constructor)

        kwargs = {
            key: self._build(val, type_hints.get(key))
            for key, val in config.items()
        }

        return constructor(*args, **kwargs)

    def _build(self, config: tp.Any, annotation: tp.Type = None) -> tp.Any:
        if annotation is not None:
            annotation = self._remove_optional(annotation)

        if annotation == tp.Any:
            annotation = None

        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", [])

        if config is None:
            return config

        if origin in (tp.List, list):
            value_cls = args[0] if args else None
            return list(self._build(x, value_cls) for x in config)

        if origin in (tp.Set, set):
            value_cls = args[0] if args else None
            return set(self._build(x, value_cls) for x in config)

        if origin in (tp.Tuple, tuple):
            if not args:
                return tuple(self._build(x) for x in config)

            if len(args) == 2 and args[1] == Ellipsis:
                return tuple(self._build(x, args[0]) for x in config)

            return tuple(
                self._build(value_config, value_cls)
                for value_config, value_cls in zip(config, args))

        if origin in (tp.Dict, dict):
            key_cls = args[0] if args else None
            value_cls = args[1] if args else None
            return {
                self._build(key_config, key_cls):
                self._build(value_config, value_cls)
                for key_config, value_config in config.items()
            }

        if origin == tp.Union:
            if not args:
                return self._build(config)

            value_config = copy.deepcopy(config)

            for value_cls in args:
                try:
                    return self._build(value_config, value_cls)
                except (ValueError, TypeError, ConfigurationError,
                        AttributeError):
                    value_config = copy.deepcopy(config)
                    continue

            raise ConfigurationError(
                f"Failed to construct argument with type {annotation}")

        if isinstance(config, (list, set, tuple)):
            T = type(config)
            value_cls = args[0] if args else None
            return T(self._build(x, value_cls) for x in config)

        if not isinstance(config, dict):
            if annotation is not None and not isinstance(config, annotation):
                raise ConfigurationError(f"type mismatch: {annotation}")
            return config

        if annotation is None and self._typekey not in config:
            return {key: self._build(val) for key, val in config.items()}

        if self._typekey in config:
            class_name = config.pop(self._typekey)
            constructor = self._get_constructor_by_name(class_name, annotation)
        else:
            constructor = origin or annotation  # type: ignore

        return self._construct_with_args(constructor, config)
