import io
import sys
import traceback
import typing
from collections import abc
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
    overload,
)

if sys.version_info >= (3, 10):
    from types import UnionType
else:

    class UnionType:
        ...


from colt.default_registry import DefaultRegistry
from colt.error import ConfigurationError
from colt.lazy import Lazy
from colt.registrable import Registrable
from colt.utils import indent

T = TypeVar("T")


class ColtBuilder:
    _DEFAULT_TYPEKEY: Final = "@type"
    _DEFAULT_ARGSKEY: Final = "*"

    def __init__(
        self,
        typekey: Optional[str] = None,
        argskey: Optional[str] = None,
    ) -> None:
        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY

    @overload
    def __call__(self, config: Any) -> Any:
        ...

    @overload
    def __call__(self, config: Any, cls: Type[T]) -> T:
        ...

    @overload
    def __call__(self, config: Any, cls: None = ...) -> Any:
        ...

    def __call__(self, config: Any, cls: Optional[Type[T]] = None) -> Union[T, Any]:
        return self._build(config, "", cls)

    @staticmethod
    def _remove_optional(annotation: type) -> type:
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        if origin == Union and len(args) == 2 and args[1] == type(None):  # noqa: E721
            return cast(type, args[0])
        return annotation

    @staticmethod
    def _get_constructor_by_name(
        name: str,
        param_name: str,
        annotation: Optional[Type[T]] = None,
    ) -> Union[Type[T], Callable[..., T]]:
        if annotation and issubclass(annotation, Registrable):
            constructor = cast(Type[T], annotation.by_name(name))
        else:
            constructor = cast(Type[T], DefaultRegistry.by_name(name))

        if constructor is None:
            raise ConfigurationError(f"[{param_name}] type not found error: {name}")

        return constructor

    @staticmethod
    def _catname(parent: str, *keys: Union[int, str]) -> str:
        key = ".".join(str(x) for x in keys)
        return f"{parent}.{key}" if parent else key

    def _construct_with_args(
        self,
        constructor: Callable[..., T],
        config: Dict[str, Any],
        param_name: str,
        raise_configuration_error: bool = True,
    ) -> T:
        if not config:
            return constructor()

        args_config = config.get(self._argskey, [])
        if self._argskey in config:
            del config[self._argskey]

        if not isinstance(args_config, (list, tuple)):
            raise ConfigurationError(
                f"[{param_name}] Arguments must be a list or tuple."
            )
        args: List[Any] = [
            self._build(val, self._catname(param_name, self._argskey, i))
            for i, val in enumerate(args_config)
        ]

        if isinstance(constructor, type):
            type_hints = get_type_hints(  # type: ignore
                getattr(constructor, "__init__"),  # noqa: B009
            )
        else:
            type_hints = get_type_hints(constructor)

        kwargs: Dict[str, Any] = {
            key: self._build(val, self._catname(param_name, key), type_hints.get(key))
            for key, val in config.items()
        }

        try:
            return constructor(*args, **kwargs)
        except Exception as e:
            if raise_configuration_error:
                raise ConfigurationError(
                    f"[{param_name}] Failed to construct object with constructor {constructor}."
                ) from e
            else:
                raise

    def _build(
        self,
        config: Any,
        param_name: str,
        annotation: Optional[Type[T]] = None,
        raise_configuration_error: bool = True,
    ) -> Union[T, Any]:
        if annotation is not None:
            annotation = self._remove_optional(annotation)

        if annotation == Any:
            annotation = None

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        if config is None:
            return config

        if origin in (List, list):
            value_cls = args[0] if args else None
            return list(
                self._build(x, self._catname(param_name, i), value_cls)
                for i, x in enumerate(config)
            )

        if origin in (Set, set):
            value_cls = args[0] if args else None
            return set(
                self._build(x, self._catname(param_name, i), value_cls)
                for i, x in enumerate(config)
            )

        if origin in (Tuple, tuple):
            if not args:
                return tuple(
                    self._build(x, self._catname(param_name, i))
                    for i, x in enumerate(config)
                )

            if len(args) == 2 and args[1] == Ellipsis:
                return tuple(
                    self._build(x, self._catname(param_name, i), args[0])
                    for i, x in enumerate(config)
                )

            if isinstance(config, abc.Sized) and len(config) != len(args):
                raise ConfigurationError(
                    f"[{param_name}] Tuple sizes of the given config and annotation "
                    f"are mismatched: {config} / {args}"
                )

            return tuple(
                self._build(value_config, self._catname(param_name, i), value_cls)
                for i, (value_config, value_cls) in enumerate(zip(config, args))
            )

        if origin in (Dict, dict):
            key_cls = args[0] if args else None
            value_cls = args[1] if args else None
            return {
                self._build(
                    key_config, self._catname(param_name, f"[key:{i}]"), key_cls
                ): self._build(
                    value_config, self._catname(param_name, key_config), value_cls
                )
                for i, (key_config, value_config) in enumerate(config.items())
            }

        if origin == Literal:
            if config not in args:
                raise ConfigurationError(
                    f"[{param_name}] {config} is not a valid literal value."
                )
            return config

        if origin in (Union, UnionType):
            if not args:
                return self._build(config, param_name)

            trial_exceptions: List[Tuple[Any, Exception, str]] = []
            for value_cls in args:
                try:
                    return self._build(
                        config, param_name, value_cls, raise_configuration_error=False
                    )
                except (ValueError, TypeError, ConfigurationError, AttributeError) as e:
                    with io.StringIO() as fp:
                        traceback.print_exc(file=fp)
                        tb = fp.getvalue()
                    trial_exceptions.append((value_cls, e, tb))
                    continue

            trial_messages = [
                f"[{param_name}] Trying to construct {annotation} with type {cls}:\n{e}\n{tb}"
                for cls, e, tb in trial_exceptions
            ]
            raise ConfigurationError(
                "\n\n"
                + "\n".join(indent(msg) for msg in trial_messages)
                + f"\n[{param_name}] Failed to construct object with type {annotation}"
            )

        if origin == Lazy:
            value_cls = args[0] if args else None
            return Lazy(config, value_cls, self)

        if isinstance(config, (list, set, tuple)):
            cls = type(config)
            value_cls = args[0] if args else None
            return cls(
                self._build(x, self._catname(param_name, i), value_cls)
                for i, x in enumerate(config)
            )

        if not isinstance(config, dict):
            if annotation is not None and not isinstance(config, annotation):
                raise ConfigurationError(
                    f"[{param_name}] Type mismatch, expected type is "
                    f"{annotation}, but actual type is {type(config)}."
                )
            return config

        if annotation is None and self._typekey not in config:
            return {
                key: self._build(val, self._catname(param_name, key))
                for key, val in config.items()
            }

        if self._typekey in config:
            class_name = config[self._typekey]
            del config[self._typekey]
            constructor = self._get_constructor_by_name(
                class_name, param_name, annotation
            )
        else:
            constructor = origin or annotation  # type: ignore

        return self._construct_with_args(
            constructor, config, param_name, raise_configuration_error
        )
