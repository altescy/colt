import io
import sys
import textwrap
import traceback
import typing
import warnings
from collections import abc
from contextlib import suppress
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    ForwardRef,
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

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:

    class GenericAlias: ...


if sys.version_info >= (3, 10):
    from types import UnionType
else:

    class UnionType: ...


if sys.version_info >= (3, 11):
    from enum import EnumType
else:
    from enum import EnumMeta as EnumType

from colt.callback import ColtCallback, MultiCallback, SkipCallback
from colt.context import ColtContext
from colt.default_registry import DefaultRegistry
from colt.error import ConfigurationError
from colt.lazy import Lazy
from colt.placeholder import Placeholder
from colt.registrable import Registrable
from colt.types import ParamPath
from colt.utils import (
    evaluate_forward_refs,
    get_path_name,
    get_typevar_map,
    infer_scope,
    is_namedtuple,
    is_typeddict,
    issubtype,
    remove_optional,
    replace_types,
    reveal_origin,
    trace_bases,
)

T = TypeVar("T")


class ColtBuilder:
    _DEFAULT_TYPEKEY: Final = "@type"
    _DEFAULT_ARGSKEY: Final = "*"

    def __init__(
        self,
        typekey: Optional[str] = None,
        argskey: Optional[str] = None,
        strict: bool = False,
        callback: Optional[Union[ColtCallback, Sequence[ColtCallback]]] = None,
    ) -> None:
        if isinstance(callback, abc.Sequence):
            callback = MultiCallback(*callback)

        self._typekey = typekey or ColtBuilder._DEFAULT_TYPEKEY
        self._argskey = argskey or ColtBuilder._DEFAULT_ARGSKEY
        self._strict = strict
        self._callback = callback

    @property
    def typekey(self) -> str:
        return self._typekey

    @property
    def argskey(self) -> str:
        return self._argskey

    @property
    def strict(self) -> bool:
        return self._strict

    @property
    def callback(self) -> Optional[ColtCallback]:
        return self._callback

    @overload
    def __call__(self, config: Any) -> Any: ...

    @overload
    def __call__(self, config: Any, cls: Type[T]) -> T: ...

    @overload
    def __call__(self, config: Any, cls: Callable[..., T]) -> T: ...

    @overload
    def __call__(self, config: Any, cls: None = ...) -> Any: ...

    def __call__(
        self,
        config: Any,
        cls: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Union[T, Any]:
        context = ColtContext(config=config)
        if self._callback is not None:
            with suppress(SkipCallback):
                config = self._callback.on_start(config, self, context, cls)
        return self._build(config, (), cls, context=context)

    def dry_run(
        self,
        config: Any,
        cls: Optional[Union[Type[T], Callable[..., T]]] = None,
        *,
        path: ParamPath = (),
        context: Optional[ColtContext] = None,
    ) -> Union[T, Any]:
        context = context or ColtContext(config=config)
        if self._callback is not None:
            with suppress(SkipCallback):
                config = self._callback.on_start(config, self, context, cls)
        return self._build(config, path, cls, context=context, skip_construction=True)

    @staticmethod
    def _get_constructor_by_name(
        name: str,
        path: ParamPath,
        annotation: Optional[Union[Type[T], Callable[..., T], Any]] = None,
        allow_to_import: bool = True,
    ) -> Union[Type[T], Callable[..., T]]:
        origin: Any
        if isinstance(annotation, type):
            origin = annotation
        else:
            origin = reveal_origin(annotation) if annotation else None
        if origin is not None and isinstance(origin, type) and issubclass(origin, Registrable):
            constructor = cast(Type[T], origin.by_name(name, allow_to_import))
        else:
            constructor = cast(Type[T], DefaultRegistry.by_name(name, allow_to_import))
        if constructor is None:
            raise ConfigurationError(f"[{get_path_name(path)}] type not found error: {name}")
        return constructor

    def _get_constructor(
        self,
        config: Any,
        path: ParamPath,
        annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
    ) -> Optional[Union[Type[T], Callable[..., T]]]:
        if not isinstance(config, Mapping):
            return None
        if self._typekey not in config:
            return None
        name = config[self._typekey]
        if not isinstance(name, str):
            return None
        return self._get_constructor_by_name(
            name,
            path,
            annotation,
            allow_to_import=not self._strict,
        )

    def _construct_args(
        self,
        constructor: Callable[..., T],
        config: Mapping[str, Any],
        path: ParamPath,
        *,
        context: ColtContext,
        skip_construction: bool = False,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        if not config:
            return [], {}

        args_config = config.get(self._argskey, [])
        if self._argskey in config:
            config = dict(config)
            config.pop(self._argskey)

        if not isinstance(args_config, (list, tuple)):
            raise ConfigurationError(f"[{get_path_name(path)}] Arguments must be a list or tuple.")

        args: List[Any] = [
            self._build(
                val,
                path + (self._argskey, i),
                context=context,
                skip_construction=skip_construction,
            )
            for i, val in enumerate(args_config)
        ]

        if isinstance(constructor, type):
            try:  # type: ignore[unreachable]
                if is_typeddict(constructor):
                    type_hints = get_type_hints(constructor)
                else:
                    type_hints = get_type_hints(
                        getattr(constructor, "__init__"),  # noqa: B009
                    )
            except NameError:
                type_hints = constructor.__init__.__annotations__  # type: ignore[misc]
        else:
            try:
                type_hints = get_type_hints(constructor)
            except NameError:
                type_hints = constructor.__annotations__

        typevar_map: Dict[TypeVar, Any] = {}

        def get_annotation(key: str) -> Any:
            annotaiton = type_hints.get(key)
            return replace_types(annotaiton, typevar_map)

        def update_typevar(obj: Any, annotation: Any) -> Any:
            cls = type(obj)
            scope = infer_scope(cls)
            annotation_typevar_map = {k: v for k, v in get_typevar_map(annotation).items() if isinstance(v, TypeVar)}
            for cls_ in trace_bases(cls):
                for type_var, type_ in get_typevar_map(cls_).items():
                    if isinstance(type_, ForwardRef):
                        type_ = evaluate_forward_refs(type_, globals(), scope)
                    type_var = annotation_typevar_map.get(type_var, type_var)
                    typevar_map[type_var] = type_

        kwargs: Dict[str, Any] = {}
        for key, val in config.items():
            annotation = get_annotation(key)
            obj = self._build(
                val,
                path + (key,),
                annotation,
                context=context,
                skip_construction=skip_construction,
            )
            kwargs[key] = obj
            update_typevar(obj, annotation)

        return args, kwargs

    def _build(
        self,
        config: Any,
        path: ParamPath,
        annotation: Optional[Union[Type[T], Callable[..., T], Any]] = None,
        *,
        context: ColtContext,
        raise_configuration_error: bool = True,
        skip_construction: bool = False,
    ) -> Union[T, Any]:
        if self._callback is not None:
            with suppress(SkipCallback):
                config = self._callback.on_build(path, config, self, context, annotation)

        if annotation is not None and isinstance(annotation, type):
            annotation = remove_optional(annotation)

        if annotation == Any:
            annotation = None

        if isinstance(config, Placeholder):
            if annotation is not None and not config.match_type_hint(annotation):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Placeholder type mismatch: expected {annotation}, got {config.type_hint}"
                )
            return config

        if self._strict and annotation is None:
            warnings.warn(
                f"[{get_path_name(path)}] Given config is not constructed because currently "
                "strict mode is enabled and the type annotation is not given.",
                UserWarning,
            )
            return config

        origin = reveal_origin(annotation)
        args = typing.get_args(annotation)

        if config is None:
            return config

        if (
            origin
            in (
                List,
                list,
                Sequence,
                abc.Sequence,
                abc.MutableSequence,
            )
            and isinstance(config, abc.Iterable)
            and not isinstance(config, abc.Mapping)
        ):
            value_cls = args[0] if args else None
            return list(
                self._build(
                    x,
                    path + (i,),
                    value_cls,
                    context=context,
                    skip_construction=skip_construction,
                )
                for i, x in enumerate(config)
            )

        if origin in (Set, set, abc.Set) and isinstance(config, abc.Iterable) and not isinstance(config, abc.Mapping):
            value_cls = args[0] if args else None
            return set(
                self._build(
                    x,
                    path + (i,),
                    value_cls,
                    context=context,
                    skip_construction=skip_construction,
                )
                for i, x in enumerate(config)
            )

        if origin in (Tuple, tuple) and isinstance(config, abc.Iterable) and not isinstance(config, abc.Mapping):
            if not args:
                return tuple(
                    self._build(
                        x,
                        path + (i,),
                        context=context,
                        skip_construction=skip_construction,
                    )
                    for i, x in enumerate(config)
                )

            if len(args) == 2 and args[1] == Ellipsis:
                return tuple(
                    self._build(
                        x,
                        path + (i,),
                        args[0],
                        context=context,
                        skip_construction=skip_construction,
                    )
                    for i, x in enumerate(config)
                )

            if isinstance(config, abc.Sized) and len(config) != len(args):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Tuple sizes of the given config and annotation "
                    f"are mismatched: {config} / {args}"
                )

            return tuple(
                self._build(value_config, path + (i,), value_cls, context=context)
                for i, (value_config, value_cls) in enumerate(zip(config, args))
            )

        if (
            origin in (Dict, dict, abc.Mapping, abc.MutableMapping)
            and isinstance(config, abc.Mapping)
            and self._typekey not in config
        ):
            key_cls = args[0] if args else None
            value_cls = args[1] if args else None
            return {
                self._build(
                    key_config,
                    path + (f"[key:{i}]",),
                    key_cls,
                    context=context,
                    skip_construction=skip_construction,
                ): self._build(
                    value_config,
                    path + (key_config,),
                    value_cls,
                    context=context,
                    skip_construction=skip_construction,
                )
                for i, (key_config, value_config) in enumerate(config.items())
            }

        if origin == Literal:
            if config not in args:
                raise ConfigurationError(f"[{get_path_name(path)}] {config} is not a valid literal value.")
            return config

        if annotation and is_namedtuple(annotation) and isinstance(config, abc.Mapping) and self._typekey not in config:
            type_hints = get_type_hints(annotation)
            kwargs = {
                key: self._build(
                    value_config,
                    path + (key,),
                    type_hints.get(key),
                    context=context,
                    skip_construction=skip_construction,
                )
                for key, value_config in config.items()
            }
            if skip_construction:
                return None
            return annotation(**kwargs)

        if annotation and isinstance(annotation, EnumType):
            try:
                return annotation(config)
            except ValueError as e:
                if raise_configuration_error:
                    raise ConfigurationError(
                        f"[{get_path_name(path)}] Failed to construct object with type {annotation}."
                    ) from e
                else:
                    raise

        if origin in (Union, UnionType):
            if not args:
                return self._build(config, path, context=context, skip_construction=skip_construction)

            trial_exceptions: List[Tuple[Any, Exception, str]] = []
            for value_cls in args:
                try:
                    return self._build(
                        config,
                        path,
                        value_cls,
                        context=context,
                        raise_configuration_error=False,
                        skip_construction=skip_construction,
                    )
                except (ValueError, TypeError, ConfigurationError, AttributeError) as e:
                    with io.StringIO() as fp:
                        traceback.print_exc(file=fp)
                        tb = fp.getvalue()
                    trial_exceptions.append((value_cls, e, tb))
                    continue

            trial_messages = [
                f"[{get_path_name(path)}] Trying to construct {annotation} with type {cls}:\n{e}\n{tb}"
                for cls, e, tb in trial_exceptions
            ]
            raise ConfigurationError(
                "\n\n"
                + "\n".join(textwrap.indent(msg, "  ") for msg in trial_messages)
                + f"\n[{get_path_name(path)}] Failed to construct object with type {annotation}"
            )

        if origin == Lazy:
            value_cls = args[0] if args else None
            return Lazy(config, path, context, value_cls, self)

        if isinstance(config, (list, set, tuple)):
            if origin is not None and not isinstance(config, origin):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Type mismatch, expected type is "
                    f"{origin}, but actual type is {type(config)}."
                )
            if (
                isinstance(annotation, type)
                and not isinstance(annotation, GenericAlias)
                and not isinstance(config, annotation)
            ):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Type mismatch, expected type is "
                    f"{annotation}, but actual type is {type(config)}."
                )
            cls = type(config)
            value_cls = args[0] if args else None
            return cls(
                self._build(
                    x,
                    path + (i,),
                    value_cls,
                    context=context,
                    skip_construction=skip_construction,
                )
                for i, x in enumerate(config)
            )

        if isinstance(annotation, type) and issubclass(annotation, (float, complex)) and isinstance(config, int):
            return annotation(config)

        if (
            origin is not None
            and not is_typeddict(origin)
            and isinstance(origin, type)
            and isinstance(config, origin)
            and not (isinstance(config, Mapping) and self._typekey in config)
        ):
            return config

        if not isinstance(config, abc.Mapping):
            if origin is not None and not isinstance(config, origin):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Type mismatch, expected type is "
                    f"{origin}, but actual type is {type(config)}."
                )
            if (
                isinstance(annotation, type)
                and not isinstance(annotation, GenericAlias)
                and not isinstance(config, annotation)
            ):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Type mismatch, expected type is "
                    f"{annotation}, but actual type is {type(config)}."
                )
            return config

        if annotation is None and self._typekey not in config:
            return {
                key: self._build(
                    val,
                    path + (key,),
                    context=context,
                    skip_construction=skip_construction,
                )
                for key, val in config.items()
            }

        if not origin and isinstance(annotation, TypeVar):
            return self._build(
                config,
                path,
                annotation.__bound__,
                context=context,
                skip_construction=skip_construction,
            )

        if self._typekey in config:
            config = dict(config)
            class_name = config.pop(self._typekey)
            constructor: Union[Type[T], Callable[..., T]] = self._get_constructor_by_name(
                class_name, path, annotation, allow_to_import=not self._strict
            )
        else:
            constructor = origin or annotation  # type: ignore

        if origin == abc.Callable:
            if not issubtype(constructor, annotation):
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Type mismatch, expected type is {type}, but actual type is {constructor}."
                )
        elif (
            annotation is not None
            and isinstance(constructor, type)
            and isinstance(annotation, type)
            and not is_typeddict(constructor)
            and not issubclass(constructor, annotation)
        ):
            raise ConfigurationError(
                f"[{get_path_name(path)}] Type mismatch, expected type is "
                f"{annotation}, but actual type is {constructor}."
            )

        args_for_constructor, kwargs_for_constructor = self._construct_args(
            constructor,
            config,
            path,
            context=context,
            skip_construction=skip_construction,
        )

        if skip_construction:
            return None

        try:
            return constructor(*args_for_constructor, **kwargs_for_constructor)
        except Exception as e:
            if raise_configuration_error:
                raise ConfigurationError(
                    f"[{get_path_name(path)}] Failed to construct object with constructor {constructor}."
                ) from e
            else:
                raise
