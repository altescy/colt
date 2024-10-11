import dataclasses
import typing
from typing import Any, Dict, Type

if typing.TYPE_CHECKING:
    from colt.callback import ColtCallback


CallbackState = Dict[Type["ColtCallback"], Dict[str, Any]]


@dataclasses.dataclass
class ColtContext:
    config: Any
    state: Dict[str, Any] = dataclasses.field(default_factory=dict)
