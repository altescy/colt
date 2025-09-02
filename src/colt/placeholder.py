from typing import Any, Generic, TypeVar

from colt.utils import issubtype

T = TypeVar("T")


class Placeholder(Generic[T]):
    def __init__(self, annotation: T) -> None:
        self._annotation = annotation

    @property
    def type_hint(self) -> T:
        return self._annotation

    def match_type_hint(self, annotation: Any) -> bool:
        return issubtype(self._annotation, annotation)
