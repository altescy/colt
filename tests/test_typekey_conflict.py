import colt


class FooWithTypeArg:
    def __init__(self, type: str) -> None:
        self.type = type


class BarWithTypeArg:
    def __init__(self, type: str, value: int) -> None:
        self.type = type
        self.value = value


class Baz:
    def __init__(self, value: int) -> None:
        self.value = value


def test_build_with_typekey_conflict() -> None:
    obj = colt.build({"type": "hello"}, FooWithTypeArg, typekey="type")
    assert isinstance(obj, FooWithTypeArg)
    assert obj.type == "hello"


def test_build_with_typekey_conflict_and_other_args() -> None:
    obj = colt.build({"type": "world", "value": 42}, BarWithTypeArg, typekey="type")
    assert isinstance(obj, BarWithTypeArg)
    assert obj.type == "world"
    assert obj.value == 42


def test_build_with_typekey_as_type_indicator() -> None:
    colt.register("baz_for_typekey_test")(Baz)
    obj = colt.build({"type": "baz_for_typekey_test", "value": 123}, typekey="type")
    assert isinstance(obj, Baz)
    assert obj.value == 123


def test_build_typekey_fallback_to_mapping() -> None:
    from typing import Mapping, Union

    obj = colt.build({"type": "text"}, Union[dict, Mapping], typekey="type")
    assert obj == {"type": "text"}

    obj = colt.build({"type": "text"}, dict, typekey="type")
    assert obj == {"type": "text"}


def test_build_list_of_dicts_with_typekey() -> None:
    from typing import Any, Dict, List

    value = [{"type": "text", "text": "hello"}]

    obj = colt.build(value, List[Dict[str, Any]], typekey="type")
    assert obj == [{"type": "text", "text": "hello"}]


def test_build_typekey_in_untyped_context_is_kept_as_data() -> None:
    from typing import Any, Dict

    import pytest

    from colt.error import ConfigurationError

    # Any / no annotation with an unregistered typekey value -> treat as plain data.
    kept: Any = colt.build({"type": "text", "text": "hi", "extra": 1}, Any, typekey="type")
    assert kept == {"type": "text", "text": "hi", "extra": 1}
    assert list(kept) == ["type", "text", "extra"]  # original key order preserved
    assert colt.build({"type": "text", "text": "hi"}, typekey="type") == {"type": "text", "text": "hi"}
    assert colt.build({"content": [{"type": "text", "text": "hi"}]}, Dict[str, Any], typekey="type") == {
        "content": [{"type": "text", "text": "hi"}]
    }

    # A registered typekey value must still dispatch, even under Any.
    colt.register("baz_untyped_dispatch")(Baz)
    assert isinstance(colt.build({"type": "baz_untyped_dispatch", "value": 1}, Any, typekey="type"), Baz)

    # A concrete annotation with an unregistered typekey value must still raise.
    with pytest.raises(ConfigurationError):
        colt.build({"type": "not_registered"}, Baz, typekey="type")
