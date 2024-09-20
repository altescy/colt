from typing import Any

from colt.utils import issubtype


class Placeholder:
    def __init__(self, annotation: Any) -> None:
        self._annotation = annotation

    @property
    def type_hint(self) -> Any:
        return self._annotation

    def match_type_hint(self, annotation: Any) -> bool:
        return issubtype(annotation, self._annotation)
