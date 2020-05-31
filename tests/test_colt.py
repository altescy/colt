import typing as tp

import colt


@colt.register("foo")
class Foo:
    def __init__(self, x: str) -> None:
        self.x = x


@colt.register("bar")
class Bar:
    def __init__(self, foos: tp.List[Foo]) -> None:
        self.foos = foos


@colt.register("baz")
class Baz(Foo):
    def __init__(self, x: str, y: int = None) -> None:
        super().__init__(x)
        self.y = y


@colt.register("qux")
class Qux:
    def __init__(self, x: tp.Set[int]) -> None:
        self.x = x


@colt.register("corge")
class Corge:
    def __init__(self, x) -> None:
        self.x = x


@colt.register("grault")
class Grault:
    def __init__(self, x: tp.Tuple[Foo, Qux]) -> None:
        self.x = x


@colt.register("garply")
class Garply:
    def __init__(self, x: tp.Dict[str, Foo]) -> None:
        self.x = x


@colt.register("waldo")
class Waldo:
    def __init__(self, x: tp.Union[str, Foo]) -> None:
        self.x = x


@colt.register("fred")
class Fred:
    def __init__(self, x: tp.Any) -> None:
        self.x = x


def test_colt_with_type():
    config = {
        "bar": {
            "@type":
            "bar",
            "foos": [
                {
                    "@type": "foo",
                    "x": "hello"
                },
                {
                    "@type": "foo",
                    "x": "world"
                },
            ]
        },
        "foos": [
            {
                "@type": "foo",
                "x": "hoge"
            },
            {
                "@type": "foo",
                "x": "fuga"
            },
        ]
    }

    obj = colt.build(config)

    assert isinstance(obj["bar"], Bar)
    assert isinstance(obj["bar"].foos, list)
    assert isinstance(obj["bar"].foos[0], Foo)
    assert isinstance(obj["foos"], list)
    assert isinstance(obj["foos"][0], Foo)


def test_colt_with_less_type():
    config = {
        "@type": "bar",
        "foos": [
            {
                "x": "hello"
            },
            {
                "x": "world"
            },
        ]
    }

    obj = colt.build(config)

    assert isinstance(obj, Bar)
    assert isinstance(obj.foos, list)
    assert isinstance(obj.foos[0], Foo)


def test_colt_with_optional():
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
        "y": 123,
    }

    obj = colt.build(config)

    assert obj.y == 123


def test_colt_with_subclass():
    config = {
        "@type": "bar",
        "foos": [
            {
                "x": "hello"
            },
            {
                "@type": "baz",
                "x": "world",
                "y": 123
            },
        ]
    }

    obj = colt.build(config)

    assert isinstance(obj, Bar)
    assert isinstance(obj.foos[0], Foo)
    assert isinstance(obj.foos[1], Baz)


def test_type_conversion():
    config = {
        "@type": "qux",
        "x": [1, 2, 3, 3],
    }

    obj = colt.build(config)

    assert isinstance(obj, Qux)
    assert isinstance(obj.x, set)
    assert len(obj.x) == 3


def test_colt_without_annotation():
    config = {
        "@type": "corge",
        "x": ["a", "b"],
    }

    obj = colt.build(config)

    assert isinstance(obj, Corge)
    assert isinstance(obj.x, list)
    assert isinstance(obj.x[0], str)


def test_colt_tuple():
    config = {
        "@type": "grault",
        "x": [
            {
                "x": "hello"
            },
            {
                "x": [1, 2, 3]
            },
        ]
    }

    obj = colt.build(config)

    assert isinstance(obj, Grault)
    assert isinstance(obj.x, tuple)
    assert isinstance(obj.x[0], Foo)
    assert isinstance(obj.x[1], Qux)


def test_colt_dict():
    config = {
        "@type": "garply",
        "x": {
            "a": {
                "x": "hello"
            },
            "b": {
                "x": "world"
            },
        }
    }

    obj = colt.build(config)

    assert isinstance(obj, Garply)
    assert isinstance(obj.x, dict)
    assert isinstance(obj.x["a"], Foo)
    assert isinstance(obj.x["b"], Foo)
    assert obj.x["a"].x == "hello"
    assert obj.x["b"].x == "world"


def test_colt_union():
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
        "x": {
            "x": "hello"
        },
    }

    obj = colt.build(config)

    assert isinstance(obj, Waldo)
    assert isinstance(obj.x, Foo)
    assert obj.x.x == "hello"


def test_colt_any():
    config = {"@type": "fred", "x": {"@type": "foo", "x": "hello"}}

    obj = colt.build(config)

    assert isinstance(obj.x, Foo)
