import dataclasses
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

from colt import ColtBuilder, ColtCallback, ColtContext, Lazy
from colt.types import ParamPath

T = TypeVar("T")


def test_callback_with_context() -> None:
    @dataclasses.dataclass
    class Value:
        value: int

    @dataclasses.dataclass
    class Result:
        total: int

    @dataclasses.dataclass
    class Container:
        values: List[Value]
        result: Lazy[Result]

    class CalcCallback(ColtCallback):
        def on_build(
            self,
            path: ParamPath,
            config: Any,
            builder: ColtBuilder,
            context: ColtContext,
            annotation: Optional[Union[Type[T], Callable[..., T]]] = None,
        ) -> Any:
            if annotation is Value:
                context.state["total"] = context.state.get("total", 0) + config["value"]
                return config
            elif annotation is Result:
                return {**config, "total": context.state["total"]}
            return config

    builder = ColtBuilder(callback=CalcCallback())

    config = {
        "values": [{"value": 1}, {"value": 2}, {"value": 3}],
        "result": {},
    }
    container = builder(config, Container)

    result = container.result.construct()

    assert isinstance(result, Result)
    assert result.total == 6
