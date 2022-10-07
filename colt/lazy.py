import typing
from typing import Any, Generic, Optional, Type, TypeVar, Union

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder

T = TypeVar("T")


class Lazy(Generic[T]):
    def __init__(
        self,
        config: Any,
        cls: Optional[Type[T]] = None,
        param_name: Optional[str] = None,
        builder: Optional["ColtBuilder"] = None,
    ) -> None:
        self._cls = cls
        self._config = config or {}
        self._param_name = param_name or ""
        self._builder = builder or ColtBuilder()

    def construct(self, **kwargs: Any) -> T:
        config = {**self._config, **kwargs}
        return self._builder(config, self._cls)
