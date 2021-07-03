# pylint: disable=too-many-return-statements,too-many-branches
import copy
import io
import traceback
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from colt.default_registry import DefaultRegistry
from colt.error import ConfigurationError
from colt.registrable import Registrable

T = TypeVar("T")


class ColtBuilder:
    _DEFAULT_TYPEKEY = "@type"
    _DEFAULT_ARGSKEY = "*"

    def __init__(
        self, typekey: Optional[str] = None, argskey: Optional[str] = None
    ) -> None:
        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY

    def __call__(self, config: Any, cls: Optional[Type[T]] = None) -> Union[T, Any]:
        return self._build(config, "", cls)

    @staticmethod
    def _remove_optional(annotation: type) -> type:
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", ())
        if origin == Union and len(args) == 2 and args[1] == type(None):  # noqa: E721
            return cast(type, args[0])
        return annotation

    @staticmethod
    def _get_constructor_by_name(
        name: str, param_name: str, annotation: Optional[Type[T]] = None
    ) -> Union[Type[T], Callable[..., T]]:
        if annotation and issubclass(annotation, Registrable):
            constructor = cast(Type[T], annotation.by_name(name))
        else:
            constructor = cast(Type[T], DefaultRegistry.by_name(name))

        if constructor is None:
            raise ConfigurationError(f"type not found error at `{param_name}`: {name}")

        return constructor

    def _construct_with_args(
        self,
        constructor: Callable[..., T],
        config: Dict[str, Any],
        param_name: str,
    ) -> T:
        if not config:
            return constructor()

        args_config = config.pop(self._argskey, [])
        if not isinstance(args_config, (list, tuple)):
            raise ConfigurationError(f"args must be a list or tuple: {param_name}")
        args: List[Any] = [
            self._build(val, param_name + f".{self._argskey}.{i}")
            for i, val in enumerate(args_config)
        ]

        if isinstance(constructor, type):
            type_hints = get_type_hints(  # type: ignore
                getattr(constructor, "__init__"),  # noqa: B009
            )
        else:
            type_hints = get_type_hints(constructor)

        kwargs: Dict[str, Any] = {
            key: self._build(val, param_name + f".{key}", type_hints.get(key))
            for key, val in config.items()
        }

        try:
            return constructor(*args, **kwargs)
        except Exception as e:
            raise ConfigurationError(f"Failed to construct at {param_name}") from e

    def _build(
        self,
        config: Any,
        param_name: str,
        annotation: Optional[Type[T]] = None,
    ) -> Union[T, Any]:
        config = copy.deepcopy(config)

        if annotation is not None:
            annotation = self._remove_optional(annotation)

        if annotation == Any:
            annotation = None

        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", [])

        if config is None:
            return config

        if origin in (List, list):
            value_cls = args[0] if args else None
            return list(
                self._build(x, param_name + f".{i}", value_cls)
                for i, x in enumerate(config)
            )

        if origin in (Set, set):
            value_cls = args[0] if args else None
            return set(
                self._build(x, param_name + f".{i}", value_cls)
                for i, x in enumerate(config)
            )

        if origin in (Tuple, tuple):
            if not args:
                return tuple(
                    self._build(x, param_name + f".{i}") for i, x in enumerate(config)
                )

            if len(args) == 2 and args[1] == Ellipsis:
                return tuple(
                    self._build(x, param_name + f".{i}", args[0])
                    for i, x in enumerate(config)
                )

            return tuple(
                self._build(value_config, param_name + f".{i}", value_cls)
                for i, (value_config, value_cls) in enumerate(zip(config, args))
            )

        if origin in (Dict, dict):
            key_cls = args[0] if args else None
            value_cls = args[1] if args else None
            return {
                self._build(
                    key_config, param_name + f".[key:{i}]", key_cls
                ): self._build(value_config, param_name + f".{key_config}", value_cls)
                for i, (key_config, value_config) in enumerate(config.items())
            }

        if origin == Union:
            if not args:
                return self._build(config, param_name)

            trial_exceptions: List[Tuple[Any, Exception, str]] = []
            for value_cls in args:
                try:
                    return self._build(config, param_name, value_cls)
                except (ValueError, TypeError, ConfigurationError, AttributeError) as e:
                    with io.StringIO() as fp:
                        traceback.print_exc(file=fp)
                        tb = fp.getvalue()
                    trial_exceptions.append((value_cls, e, tb))
                    continue

            trial_messages = [
                f"-----  Trial exception ({cls}):\n{repr(e)}\n{tb}"
                for cls, e, tb in trial_exceptions
            ]
            raise ConfigurationError(
                f"Failed to construct argument {param_name} with type {annotation}\n\n"
                + "\n".join(msg for msg in trial_messages)
            )

        if isinstance(config, (list, set, tuple)):
            cls = type(config)
            value_cls = args[0] if args else None
            return cls(
                self._build(x, param_name + f".{i}", value_cls)
                for i, x in enumerate(config)
            )

        if not isinstance(config, dict):
            if annotation is not None and not isinstance(config, annotation):
                raise ConfigurationError(
                    f"type mismatch at {param_name}, expected: "
                    f"{annotation}, actual type: {type(config)}"
                )
            return config

        if annotation is None and self._typekey not in config:
            return {
                key: self._build(val, param_name + f".{key}")
                for key, val in config.items()
            }

        if self._typekey in config:
            class_name = config.pop(self._typekey)
            constructor = self._get_constructor_by_name(
                class_name, param_name, annotation
            )
        else:
            constructor = origin or annotation  # type: ignore

        return self._construct_with_args(constructor, config, param_name)
