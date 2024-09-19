import typing
from copy import deepcopy
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from colt.utils import update_field

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder

T = TypeVar("T")


class Lazy(Generic[T]):
    def __init__(
        self,
        config: Any,
        param_name: str = "",
        cls: Optional[Type[T]] = None,
        builder: Optional["ColtBuilder"] = None,
    ) -> None:
        from colt.builder import ColtBuilder

        self._cls = cls
        self._config = config or {}
        self._param_name = param_name
        self._builder = builder or ColtBuilder()

        self._builder.dry_run(self._config, self._cls, param_name=self._param_name)

    @property
    def config(self) -> Any:
        return self._config

    @property
    def constructor(self) -> Optional[Union[Type[T], Callable[..., T]]]:
        return (
            self._builder._get_constructor(self._config, self._param_name, self._cls)
            or self._cls
        )

    def update(
        self,
        *args: Mapping[Union[int, str, Sequence[Union[int, str]]], Any],
        **kwargs: Any,
    ) -> None:
        for arg in args:
            for field, value in arg.items():
                update_field(self._config, field, value)
        for k, v in kwargs.items():
            update_field(self._config, k, v)
        self._builder.dry_run(self._config, self._cls, param_name=self._param_name)

    def construct(
        self,
        *args: Mapping[Union[int, str, Sequence[Union[int, str]]], Any],
        **kwargs: Any,
    ) -> T:
        if args or kwargs:
            config = deepcopy(self._config)
            for arg in args:
                for field, value in arg.items():
                    update_field(config, field, value)
            for k, v in kwargs.items():
                update_field(config, k, v)
        else:
            config = self._config
        return self._builder._build(config, self._param_name, self._cls)
