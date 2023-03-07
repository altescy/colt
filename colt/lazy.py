import typing
from typing import Any, Generic, Optional, Type, TypeVar

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

    def construct(self, **kwargs: Any) -> T:
        config = {**self._config, **kwargs}
        return self._builder._build(config, self._param_name, self._cls)
