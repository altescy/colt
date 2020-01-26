import typing as tp

import pob


@pob.register("foo")
class Foo:
    def __init__(self, x: str) -> None:
        self.x = x


@pob.register("bar")
class Bar:
    def __init__(self, foos: tp.List[Foo]) -> None:
        self.foos = foos


@pob.register("baz")
class Baz(Foo):
    def __init__(self, x: str, y: int = None) -> None:
        super().__init__(x)
        self.y = y


@pob.register("qux")
class Qux:
    def __init__(self, x: tp.Set[int]) -> None:
        self.x = x


@pob.register("corge")
class Corge:
    def __init__(self, x) -> None:
        self.x = x


class TestPob:
    @staticmethod
    def test_pob_with_type():
        config = {
            "bar": {
                "@type": "bar",
                "foos": [
                    {"@type": "foo", "x": "hello"},
                    {"@type": "foo", "x": "world"},
                ]
            },
            "foos": [
                {"@type": "foo", "x": "hoge"},
                {"@type": "foo", "x": "fuga"},
            ]
        }

        obj = pob.build(config)

        assert isinstance(obj["bar"], Bar)
        assert isinstance(obj["bar"].foos, list)
        assert isinstance(obj["bar"].foos[0], Foo)
        assert isinstance(obj["foos"], list)
        assert isinstance(obj["foos"][0], Foo)

    @staticmethod
    def test_pob_with_less_type():
        config = {
            "@type": "bar",
            "foos": [
                {"x": "hello"},
                {"x": "world"},
            ]
        }

        obj = pob.build(config)

        assert isinstance(obj, Bar)
        assert isinstance(obj.foos, list)
        assert isinstance(obj.foos[0], Foo)

    @staticmethod
    def test_pob_with_optional():
        config = {
            "@type": "baz",
            "x": "hello",
        }

        obj = pob.build(config)

        assert isinstance(obj, Baz)
        assert obj.x == "hello"
        assert obj.y == None

        config = {
            "@type": "baz",
            "x": "hello",
            "y": 123,
        }

        obj = pob.build(config)

        assert obj.y == 123

    @staticmethod
    def test_pob_with_subclass():
        config = {
            "@type": "bar",
            "foos": [
                {"x": "hello"},
                {"@type": "baz", "x": "world", "y": 123},
            ]
        }

        obj = pob.build(config)

        assert isinstance(obj, Bar)
        assert isinstance(obj.foos[0], Foo)
        assert isinstance(obj.foos[1], Baz)

    @staticmethod
    def test_type_conversion():
        config = {
            "@type": "qux",
            "x": [1, 2, 3, 3],
        }

        obj = pob.build(config)

        assert isinstance(obj, Qux)
        assert isinstance(obj.x, set)
        assert len(obj.x) == 3

    @staticmethod
    def test_pob_without_annotation():
        config = {
            "@type": "corge",
            "x": ["a", "b"],
        }

        obj = pob.build(config)

        assert isinstance(obj, Corge)
        assert isinstance(obj.x, list)
        assert isinstance(obj.x[0], str)
