import dataclasses

import colt
from colt.constructed import Constructed


def test_constructed_holds_value() -> None:
    value = {"type": "Learner"}
    wrapper = Constructed(value)
    assert wrapper.value is value


def test_constructed_value_is_not_rebuilt() -> None:
    @dataclasses.dataclass
    class Foo:
        value: dict

    value = {"type": "Learner"}
    config = {"value": Constructed(value)}
    obj = colt.build(config, Foo)
    assert obj.value is value
