from typing import Generic, TypeVar

import colt

T = TypeVar("T")


def test_generic_registrable_can_be_built() -> None:
    class Foo(colt.Registrable, Generic[T]):
        ...

    @Foo.register("bar")
    class Bar(Foo[int]):
        ...

    class Container:
        def __init__(self, foo: Foo[T]) -> None:
            self.foo = foo

    container = colt.build({"foo": {"@type": "bar"}}, Container)
    assert isinstance(container, Container)
    assert isinstance(container.foo, Bar)
