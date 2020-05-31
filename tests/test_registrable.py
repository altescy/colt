import colt


class Foo(colt.Registrable):
    pass


class Bar(colt.Registrable):
    pass


@Foo.register("baz")
class FooBaz(Foo):
    pass


@Bar.register("baz")
class BarBaz(Bar):
    pass


@colt.register("my_class")
class MyClass:
    def __init__(self, foo: Foo, bar: Bar):
        self.foo = foo
        self.bar = bar


def test_registrable():
    config = {
        "@type": "my_class",
        "foo": {
            "@type": "baz"
        },
        "bar": {
            "@type": "baz"
        }
    }

    obj = colt.build(config)

    assert isinstance(obj.foo, FooBaz)
    assert isinstance(obj.bar, BarBaz)
