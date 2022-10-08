import typing
from typing import Any, Generic, Optional, Type, TypeVar

if typing.TYPE_CHECKING:
    from colt.builder import ColtBuilder

T = TypeVar("T")


class Lazy(Generic[T]):
    def __init__(
        self,
        config: Any,
        cls: Optional[Type[T]] = None,
        builder: Optional["ColtBuilder"] = None,
    ) -> None:
        from colt.builder import ColtBuilder

        self._cls = cls
        self._config = config or {}
        self._builder = builder or ColtBuilder()

    def construct(self, **kwargs: Any) -> T:
        config = {**self._config, **kwargs}
        return self._builder(config, self._cls)
