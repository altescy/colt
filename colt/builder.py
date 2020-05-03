#pylint: disable=too-many-return-statements,too-many-branches
import typing as tp

import copy
import importlib

from colt.error import ConfigurationError
from colt.type_store import TypeStore


class ColtBuilder:
    _DEFAULT_TYPEKEY = "@type"
    _DEFAULT_ARGSKEY = "*"

    def __init__(self, typekey: str = None, argskey: str = None) -> None:
        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY

    def __call__(self, config: tp.Any) -> tp.Any:
        return self._build(config)

    @staticmethod
    def _get_external_type(type_path: str) -> tp.Any:
        module_path, type_name = type_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        T = getattr(module, type_name, None)
        return T

    @staticmethod
    def _remove_optional(annotation: type):
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())
        if origin == tp.Union and len(args) == 2 and args[1] == type(None):
            return args[0]
        return annotation

    @staticmethod
    def _construct(T: tp.Type, args: tp.List[tp.Any],
                   kwargs: tp.Dict[str, tp.Any]) -> tp.Any:
        colt_constructor = getattr(T, "_colt_constructor", None)
        if colt_constructor:
            constructor = getattr(T, colt_constructor)
            return constructor(args, kwargs)
        return T(*args, **kwargs)

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

        T = origin or annotation  # type: ignore
        if self._typekey in config:
            type_name = config.pop(self._typekey)

            try:
                T = TypeStore.get(type_name)
            except KeyError:
                T = self._get_external_type(type_name)

            if T is None:
                raise ConfigurationError(f"type not found error: {type_name}")

            if annotation is not None and not issubclass(T, annotation):
                raise ConfigurationError(
                    f"{T} is not subclass of {annotation}")

        if not config:
            return self._construct(T, {})

        args_config = config.pop(self._argskey, [])
        if not isinstance(args_config, list):
            raise ConfigurationError("args must be a list")
        args = [self._build(val) for val in args_config]

        type_hints = tp.get_type_hints(T.__init__)
        kwargs = {
            key: self._build(val, type_hints.get(key))
            for key, val in config.items()
        }
        return self._construct(T, args, kwargs)
