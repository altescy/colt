from typing import Generic, TypeVar

T = TypeVar("T")


class Constructed(Generic[T]):
    """A wrapper that marks a value as already constructed.

    colt's builder unwraps this and returns the wrapped value without trying to
    interpret it as configuration to build. Call sites create it with the value
    they want to inject, and the builder unwraps with `.value`.
    """

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        return self._value
