import io
import sys
import traceback
import typing
import warnings
from collections import abc
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
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
        strict: bool = False,
    ) -> None:
        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY
        self._strict = strict

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
        allow_to_import: bool = True,
    ) -> Union[Type[T], Callable[..., T]]:
        if (
            annotation
            and isinstance(annotation, type)
            and issubclass(annotation, Registrable)
        ):
            constructor = cast(Type[T], annotation.by_name(name, allow_to_import))
        else:
            constructor = cast(Type[T], DefaultRegistry.by_name(name, allow_to_import))

        if constructor is None:
            raise ConfigurationError(f"[{param_name}] type not found error: {name}")

        return constructor

    @staticmethod
    def _is_namedtuple(cls: Type[T]) -> bool:
        bases = getattr(cls, "__bases__", [])
        if len(bases) != 1 or bases[0] != tuple:
            return False
        fields = getattr(cls, "_fields", None)
        if not isinstance(fields, tuple):
            return False
        return all(type(name) == str for name in fields)

    @staticmethod
    def _catname(parent: str, *keys: Union[int, str]) -> str:
        key = ".".join(str(x) for x in keys)
        return f"{parent}.{key}" if parent else key

    def _construct_with_args(
        self,
        constructor: Callable[..., T],
        config: Mapping[str, Any],
        param_name: str,
        raise_configuration_error: bool = True,
    ) -> T:
        if not config:
            return constructor()

        args_config = config.get(self._argskey, [])
        if self._argskey in config:
            config = dict(config)
            config.pop(self._argskey)

        if not isinstance(args_config, (list, tuple)):
            raise ConfigurationError(
                f"[{param_name}] Arguments must be a list or tuple."
            )
        args: List[Any] = [
            self._build(val, self._catname(param_name, self._argskey, i))
            for i, val in enumerate(args_config)
        ]

        if isinstance(constructor, type):
            try:  # type: ignore[unreachable]
                type_hints = get_type_hints(
                    getattr(constructor, "__init__"),  # noqa: B009
                )
            except NameError:
                type_hints = constructor.__init__.__annotations__
        else:
            try:
                type_hints = get_type_hints(constructor)
            except NameError:
                type_hints = constructor.__annotations__

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

        if self._strict and annotation is None:
            warnings.warn(
                f"[{param_name}] Given config is not constructed because currently "
                "strict mode is enabled and the type annotation is not given.",
                UserWarning,
            )
            return config

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        if config is None:
            return config

        if origin in (List, list, Sequence, abc.Sequence, abc.MutableSequence):
            value_cls = args[0] if args else None
            return list(
                self._build(x, self._catname(param_name, i), value_cls)
                for i, x in enumerate(config)
            )

        if origin in (Set, set, abc.Set):
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

        if origin in (Dict, dict, abc.Mapping, abc.MutableMapping):
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

        if annotation and self._is_namedtuple(annotation):
            type_hints = get_type_hints(annotation)
            kwargs = {
                key: self._build(
                    value_config,
                    self._catname(param_name, key),
                    type_hints.get(key),
                )
                for key, value_config in config.items()
            }
            return annotation(**kwargs)

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
            return Lazy(config, param_name, value_cls, self)

        if isinstance(config, (list, set, tuple)):
            if origin is not None and not isinstance(config, origin):
                raise ConfigurationError(
                    f"[{param_name}] Type mismatch, expected type is "
                    f"{origin}, but actual type is {type(config)}."
                )
            if isinstance(annotation, type) and not isinstance(config, annotation):
                raise ConfigurationError(
                    f"[{param_name}] Type mismatch, expected type is "
                    f"{annotation}, but actual type is {type(config)}."
                )
            cls = type(config)
            value_cls = args[0] if args else None
            return cls(
                self._build(x, self._catname(param_name, i), value_cls)
                for i, x in enumerate(config)
            )

        if not isinstance(config, abc.Mapping):
            if origin is not None and not isinstance(config, origin):
                raise ConfigurationError(
                    f"[{param_name}] Type mismatch, expected type is "
                    f"{origin}, but actual type is {type(config)}."
                )
            if isinstance(annotation, type) and not isinstance(config, annotation):
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
            config = dict(config)
            class_name = config.pop(self._typekey)
            constructor = self._get_constructor_by_name(
                class_name, param_name, annotation, allow_to_import=not self._strict
            )
        else:
            constructor = origin or annotation  # type: ignore

        if (
            annotation is not None
            and isinstance(constructor, type)
            and isinstance(annotation, type)
            and not issubclass(constructor, annotation)
        ):
            raise ConfigurationError(
                f"[{param_name}] Type mismatch, expected type is "
                f"{annotation}, but actual type is {constructor}."
            )

        return self._construct_with_args(
            constructor, config, param_name, raise_configuration_error
        )
