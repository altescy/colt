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
