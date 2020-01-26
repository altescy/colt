#pylint: disable=too-many-return-statements,too-many-branches
import typing as tp

import copy

from pob.type_store import TypeStore


_TYPEKEY = "@type"


class ConfigurationError(Exception):
    """configuration error"""


def remove_optional(annotation: type):
    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", ())
    if origin == tp.Union and len(args) == 2 and args[1] == type(None):
        return args[0]
    return annotation


def build(config, annotation: tp.Type = None) -> tp.Any:
    if annotation is not None:
        annotation = remove_optional(annotation)

    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", [])

    if config is None:
        return config

    if origin in (tp.List, list):
        value_cls = args[0] if args else None
        return list(build(x, value_cls) for x in config)

    if origin in (tp.Set, set):
        value_cls = args[0] if args else None
        return set(build(x, value_cls) for x in config)

    if origin in (tp.Set, set):
        value_cls = args[0] if args else None
        return set(build(x, value_cls) for x in config)

    if origin in (tp.Tuple, tuple):
        if not args:
            return tuple(build(x) for x in config)

        if len(args) == 2 and args[1] == Ellipsis:
            return tuple(build(x, args[0]) for x in config)

        return [
            build(value_config, value_cls)
            for value_config, value_cls in zip(config, args)
        ]

    if origin in (tp.Dict, dict):
        key_cls = args[0] if args else None
        value_cls = args[1] if args else None
        return {
            build(key_config, key_cls): build(value_config, value_cls)
            for key_config, value_config in config.items()
        }

    if origin == tp.Union:
        if not args:
            return build(config)

        value_config = copy.deepcopy(config)

        for value_cls in args:
            try:
                return build(value_config, value_cls)
            except (ValueError, TypeError, ConfigurationError, AttributeError):
                value_config = copy.deepcopy(config)
                continue

        raise ConfigurationError(f"Failed to construct argument with type {annotation}")

    if isinstance(config, (list, set, tuple)):
        T = type(config)
        value_cls = args[0] if args else None
        return T(build(x, value_cls) for x in config)

    if not isinstance(config, dict):
        if annotation is not None and not isinstance(config, annotation):
            raise ConfigurationError(f"type mismatch: {annotation}")
        return config

    if annotation is None and _TYPEKEY not in config:
        return {key: build(val) for key, val in config.items()}

    T = origin or annotation # type: ignore
    if _TYPEKEY in config:
        type_name = config.pop(_TYPEKEY)
        T = TypeStore.get(type_name)
        if annotation is not None and not issubclass(T, annotation):
            raise ConfigurationError(f"{T} is not subclass of {annotation}")

    if not config:
        return T()

    type_hints = tp.get_type_hints(T.__init__)
    args = {
        key: build(val, type_hints.get(key))
        for key, val in config.items()
    }
    return T(**args)
