import typing
from typing import Any, Generic, Optional, Type, TypeVar, Union

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder

T = TypeVar("T")


class Lazy(Generic[T]):
    def __init__(
        self,
        builder: "ColtBuilder",
        config: Any,
        cls: Optional[Type[T]] = None,
        param_name: str = "",
    ) -> None:
        self._builder = builder
        self._cls = cls
        self._config = config or {}
        self._param_name = param_name

    def construct(self, **kwargs: Any) -> T:
        config = {**self._config, **kwargs}
        return self._builder(config, self._cls)
