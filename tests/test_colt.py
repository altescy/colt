import dataclasses
import sys
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)

import pytest

import colt

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


@colt.register("foo")
class Foo:
    def __init__(self, x: str) -> None:
        self.x = x


@colt.register("bar")
class Bar:
    def __init__(self, foos: List[Foo]) -> None:
        self.foos = foos


@colt.register("baz")
class Baz(Foo):
    def __init__(self, x: str, y: Optional[int] = None) -> None:
        super().__init__(x)
        self.y = y


@colt.register("qux")
class Qux:
    def __init__(self, x: Set[int]) -> None:
        self.x = x


@colt.register("corge")
class Corge:
    def __init__(self, x) -> None:  # type: ignore
        self.x = x


@colt.register("grault")
class Grault:
    def __init__(self, x: Tuple[Foo, Qux]) -> None:
        self.x = x


@colt.register("garply")
class Garply:
    def __init__(self, x: Dict[str, Foo]) -> None:
        self.x = x


@colt.register("waldo")
class Waldo:
    def __init__(self, x: Union[str, Foo]) -> None:
        self.x = x


@colt.register("fred")
class Fred:
    def __init__(self, x: Any) -> None:
        self.x = x


@colt.register("int2str")
class Int2Str:
    def __call__(self, value: int) -> str:
        return str(value)


def test_colt_with_type() -> None:
    config = {
        "bar": {
            "@type": "bar",
            "foos": [
                {"@type": "foo", "x": "hello"},
                {"@type": "foo", "x": "world"},
            ],
        },
        "foos": [
            {"@type": "foo", "x": "hoge"},
            {"@type": "foo", "x": "fuga"},
        ],
    }

    obj = colt.build(config)

    assert isinstance(obj["bar"], Bar)
    assert isinstance(obj["bar"].foos, list)
    assert isinstance(obj["bar"].foos[0], Foo)
    assert isinstance(obj["foos"], list)
    assert isinstance(obj["foos"][0], Foo)


def test_colt_with_less_type() -> None:
    config = {
        "@type": "bar",
        "foos": [
            {"x": "hello"},
            {"x": "world"},
        ],
    }

    obj = colt.build(config)

    assert isinstance(obj, Bar)
    assert isinstance(obj.foos, list)
    assert isinstance(obj.foos[0], Foo)


def test_colt_with_optional() -> None:
    config = {
        "@type": "baz",
        "x": "hello",
    }

    obj = colt.build(config)

    assert isinstance(obj, Baz)
    assert obj.x == "hello"
    assert obj.y is None

    config = {
        "@type": "baz",
        "x": "hello",
        "y": 123,  # type: ignore
    }

    obj = colt.build(config)

    assert obj.y == 123


def test_colt_with_subclass() -> None:
    config = {
        "@type": "bar",
        "foos": [
            {"x": "hello"},
            {"@type": "baz", "x": "world", "y": 123},
        ],
    }

    obj = colt.build(config)

    assert isinstance(obj, Bar)
    assert isinstance(obj.foos[0], Foo)
    assert isinstance(obj.foos[1], Baz)


def test_type_conversion() -> None:
    config = {
        "@type": "qux",
        "x": [1, 2, 3, 3],
    }

    obj = colt.build(config)

    assert isinstance(obj, Qux)
    assert isinstance(obj.x, set)
    assert len(obj.x) == 3


def test_colt_without_annotation() -> None:
    config = {
        "@type": "corge",
        "x": ["a", "b"],
    }

    obj = colt.build(config)

    assert isinstance(obj, Corge)
    assert isinstance(obj.x, list)
    assert isinstance(obj.x[0], str)


def test_colt_tuple() -> None:
    config = {
        "@type": "grault",
        "x": [
            {"x": "hello"},
            {"x": [1, 2, 3]},
        ],
    }

    obj = colt.build(config)

    assert isinstance(obj, Grault)
    assert isinstance(obj.x, tuple)
    assert isinstance(obj.x[0], Foo)
    assert isinstance(obj.x[1], Qux)


def test_colt_dict() -> None:
    config = {
        "@type": "garply",
        "x": {
            "a": {"x": "hello"},
            "b": {"x": "world"},
        },
    }

    obj = colt.build(config)

    assert isinstance(obj, Garply)
    assert isinstance(obj.x, dict)
    assert isinstance(obj.x["a"], Foo)
    assert isinstance(obj.x["b"], Foo)
    assert obj.x["a"].x == "hello"
    assert obj.x["b"].x == "world"


def test_colt_union() -> None:
    config = {
        "@type": "waldo",
        "x": "hello",
    }

    obj = colt.build(config)

    assert isinstance(obj, Waldo)
    assert isinstance(obj.x, str)
    assert obj.x == "hello"

    config = {
        "@type": "waldo",
        "x": {"x": "hello"},  # type: ignore
    }

    obj = colt.build(config)

    assert isinstance(obj, Waldo)
    assert isinstance(obj.x, Foo)
    assert obj.x.x == "hello"


def test_colt_any() -> None:
    config = {"@type": "fred", "x": {"@type": "foo", "x": "hello"}}

    obj = colt.build(config)

    assert isinstance(obj.x, Foo)


def test_build_with_type() -> None:
    config = {"x": "abc"}

    obj = colt.build(config, Foo)

    assert isinstance(obj, Foo)
    assert obj.x == "abc"


def test_build_literal() -> None:
    class Foo:
        def __init__(self, x: Literal["hello", "world"]) -> None:
            self.x = x

    config = {"x": "hello"}
    obj = colt.build(config, Foo)

    assert isinstance(obj, Foo)
    assert colt.build(config, Foo).x == "hello"


def test_build_with_abstract_classes() -> None:
    @dataclasses.dataclass
    class Foo:
        name: str

    @colt.register("func")
    class Func:
        def __call__(self, value: str) -> None:
            pass

    @colt.register("iter")
    class Iter:
        def __iter__(self) -> Iterator[Foo]:
            return iter([])

    @dataclasses.dataclass
    class Bar:
        func: Callable[[str], None]
        sequence: Sequence[Foo]
        mapping: Mapping[str, Foo]
        mutable_sequence: MutableSequence[Foo]
        mutable_mapping: MutableMapping[str, Foo]
        iterable: Iterable[Foo]
        iterator: Iterator[Foo]

    config = {
        "func": {"@type": "func"},
        "sequence": [{"name": "a"}, {"name": "b"}],
        "mapping": {"a": {"name": "a"}, "b": {"name": "b"}},
        "mutable_sequence": [{"name": "a"}, {"name": "b"}],
        "mutable_mapping": {"a": {"name": "a"}, "b": {"name": "b"}},
        "iterable": [{"name": "a"}, {"name": "b"}],
        "iterator": {"@type": "iter"},
    }

    output = colt.build(config, Bar)
    assert isinstance(output.func, Func)
    assert isinstance(output.sequence[0], Foo)  # type: ignore[unreachable]
    assert isinstance(output.mapping["a"], Foo)  # type: ignore[unreachable]
    assert isinstance(output.iterator, Iter)  # type: ignore[unreachable]


def test_build_with_namedtuple() -> None:
    class Item(NamedTuple):
        name: str
        foo: Foo

    class Container(NamedTuple):
        item: Union[str, Sequence[Item]]

    config = {"item": [{"name": "a", "foo": {"x": "hello"}}]}
    obj = colt.build(config, Container)

    assert isinstance(obj, Container)
    assert isinstance(obj.item[0], Item)
    assert obj.item[0].name == "a"
    assert isinstance(obj.item[0].foo, Foo)
    assert obj.item[0].foo.x == "hello"


def test_build_with_callable() -> None:
    def build_foo(x: str) -> Foo:
        return Foo(x)

    config = {"x": "hello"}
    obj = colt.build(config, build_foo)

    assert isinstance(obj, Foo)
    assert obj.x == "hello"


def test_build_typed_dict() -> None:
    @dataclasses.dataclass
    class Foo:
        x: str

    class Bar(TypedDict):
        foos: List[Foo]

    config = {
        "foos": [{"x": "hello"}, {"x": "world"}],
    }

    obj = colt.build(config, Bar)

    assert isinstance(obj, dict)
    assert isinstance(obj["foos"], list)
    assert all(isinstance(foo, Foo) for foo in obj["foos"])
    assert obj["foos"][0].x == "hello"
    assert obj["foos"][1].x == "world"


def test_build_enum() -> None:
    class MyEnum(Enum):
        FOO = "foo"
        BAR = "bar"

    class Foo:
        def __init__(self, x: Optional[MyEnum]) -> None:
            self.x = x

    config = {"x": "foo"}
    obj = colt.build(config, Foo)

    assert isinstance(obj, Foo)
    assert obj.x == MyEnum.FOO


def test_build_generic_type() -> None:
    T = TypeVar("T")
    ParamsT = TypeVar("ParamsT")

    class BaseModel(Generic[ParamsT], colt.Registrable): ...

    @BaseModel.register("mymodel")
    class MyModel(BaseModel["MyModel.Params"]):
        @dataclasses.dataclass
        class Params:
            name: str
            age: int

    class Executor:
        def __init__(self, model: BaseModel[T], params: T) -> None:
            self.model = model
            self.params = params

    config = {"model": {"@type": "mymodel"}, "params": {"name": "Alice", "age": 20}}
    executor = colt.build(config, Executor)

    assert isinstance(executor.model, MyModel)
    assert isinstance(executor.params, MyModel.Params)
    assert executor.params.name == "Alice"
    assert executor.params.age == 20


def test_build_lazy_generic_type() -> None:
    T = TypeVar("T")
    ParamsT = TypeVar("ParamsT")

    class BaseModel(Generic[ParamsT], colt.Registrable): ...

    @BaseModel.register("mymodel")
    class MyModel(BaseModel["MyModel.Params"]):
        @dataclasses.dataclass
        class Params:
            name: str
            age: int

    class Executor:
        def __init__(self, model: BaseModel[T], params: colt.Lazy[T]) -> None:
            self.model = model
            self.params = params

    config = {"model": {"@type": "mymodel"}, "params": {"name": "Alice", "age": 20}}
    executor = colt.build(config, Executor)

    assert isinstance(executor.model, MyModel)
    assert isinstance(executor.params, colt.Lazy)

    params = executor.params.construct()
    assert isinstance(params, MyModel.Params)
    assert params.name == "Alice"
    assert params.age == 20


def test_build_multi_generic_type() -> None:
    T = TypeVar("T")
    U = TypeVar("U")
    InputT = TypeVar("InputT")
    ParamsT = TypeVar("ParamsT")

    class Item: ...

    class BaseModel(Generic[InputT, ParamsT], colt.Registrable): ...

    @BaseModel.register("mymodel")
    class MyModel(BaseModel[Item, "MyModel.Params"]):
        @dataclasses.dataclass
        class Params:
            name: str
            age: int

    class Executor:
        def __init__(self, model: BaseModel[T, U], params: colt.Lazy[U], data: T) -> None:
            self.model = model
            self.params = params
            self.data = data

    config = {
        "model": {"@type": "mymodel"},
        "params": {"name": "Alice", "age": 20},
        "data": {},
    }
    executor = colt.build(config, Executor)

    assert isinstance(executor.model, MyModel)
    assert isinstance(executor.params.construct(), MyModel.Params)
    assert isinstance(executor.data, Item)


def test_build_multi_inherited_generic_type() -> None:
    T = TypeVar("T")
    U = TypeVar("U")
    InputT = TypeVar("InputT")
    ParamsT = TypeVar("ParamsT")

    class Item: ...

    class BaseModel(Generic[InputT, ParamsT], colt.Registrable): ...

    class BaseItemModel(BaseModel[Item, ParamsT], Generic[ParamsT]): ...

    @BaseModel.register("mymodel")
    class MyModel(BaseItemModel["MyModel.Params"]):
        @dataclasses.dataclass
        class Params:
            name: str
            age: int

    class Executor:
        def __init__(self, model: BaseModel[T, U], params: U, data: T) -> None:
            self.model = model
            self.params = params
            self.data = data

    config = {
        "model": {"@type": "mymodel"},
        "params": {"name": "Alice", "age": 20},
        "data": {},
    }
    executor = colt.build(config, Executor)

    assert isinstance(executor.model, MyModel)
    assert isinstance(executor.params, MyModel.Params)
    assert isinstance(executor.data, Item)


def test_build_with_annotated() -> None:
    class Foo:
        def __init__(self, x: str) -> None:
            self.x = x

    class Bar:
        def __init__(self, foo: Annotated[Foo, "test"]) -> None:
            self.foo = foo

    config = {"foo": {"x": "hello"}}
    obj = colt.build(config, Bar)

    assert isinstance(obj.foo, Foo)
    assert obj.foo.x == "hello"


def test_numerical_value_compatiblity() -> None:
    class Foo:
        def __init__(self, x: float, y: complex) -> None:
            self.x = x
            self.y = y

    config = {"x": 1, "y": 1}
    obj = colt.build(config, Foo)

    assert isinstance(obj, Foo)
    assert isinstance(obj.x, float)
    assert isinstance(obj.y, complex)
    assert obj.x == 1.0
    assert obj.y == 1.0 + 0j


def test_callable() -> None:
    class Executor:
        def __init__(self, func: Callable[[int], str]) -> None:
            self.func = func

    executor = colt.build({"func": {"@type": "int2str"}}, Executor)
    assert isinstance(executor, Executor)
    assert isinstance(executor.func, Int2Str)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_abc_callable() -> None:
    from collections.abc import Callable

    class Executor:
        def __init__(self, func: Callable[[int], str]) -> None:
            self.func = func

    executor = colt.build({"func": {"@type": "int2str"}}, Executor)
    assert isinstance(executor, Executor)
    assert isinstance(executor.func, Int2Str)


def test_mapping_or_typekey() -> None:
    obj = colt.build({"@type": "int2str"}, Union[Mapping[int, str], Callable[[int], str]])  # type: ignore[call-overload]
    assert isinstance(obj, Int2Str)
