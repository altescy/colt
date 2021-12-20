colt
===

[![CI Actions Status](https://github.com/altescy/colt/workflows/CI/badge.svg)](https://github.com/altescy/colt/actions?query=workflow%3ACI)
[![Pulish Actions Status](https://github.com/altescy/colt/workflows/publish/badge.svg)](https://github.com/altescy/colt/actions?query=workflow%3Apublish)
[![Python version](https://img.shields.io/pypi/pyversions/colt)](https://github.com/altescy/colt)
[![pypi version](https://img.shields.io/pypi/v/colt)](https://pypi.org/project/colt/)
[![license](https://img.shields.io/github/license/altescy/colt)](https://github.com/altescy/colt/blob/master/LICENSE)

## Quick Links

- [Installation](#Installation)
- [Basic Examples](#Examples)
- [kaggle Titanic Example](https://github.com/altescy/colt/tree/master/examples/titanic)

## Introduction

`colt` is a configuration utility for Python objects.
`colt` constructs Python objects from a configuration dict which is convertable into JSON.
(Inspired by [AllenNLP](https://github.com/allenai/allennlp))


## Installation

```
pip install colt
```

## Examples

#### Basic Usage

```python
import typing as tp
import colt

@colt.register("foo")
class Foo:
    def __init__(self, message: str) -> None:
        self.message = message

@colt.register("bar")
class Bar:
    def __init__(self, foos: tp.List[Foo]) -> None:
        self.foos = foos

if __name__ == "__main__":
    config = {
        "@type": "bar",  # specify type name with `@type`
        "foos": [
            {"message": "hello"},  # type of this is inferred from type-hint
            {"message": "world"},
        ]
    }

    bar = colt.build(config)

    assert isinstance(bar, Bar)

    print(" ".join(foo.message for foo in bar.foos))
        # => "hello world"
```

#### `scikit-learn` Configuration

```python
import colt

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    config = {
        # import types automatically if type name is not registerd
        "@type": "sklearn.ensemble.VotingClassifier",
        "estimators": [
            ("rfc", { "@type": "sklearn.ensemble.RandomForestClassifier",
                      "n_estimators": 10 }),
            ("svc", { "@type": "sklearn.svm.SVC",
                      "gamma": "scale" }),
        ]
    }

    X, y = load_iris(return_X_y=True)
    X_train, X_valid, y_train, y_valid = train_test_split(X, y)

    model = colt.build(config)
    model.fit(X_train, y_train)

    valid_accuracy = model.score(X_valid, y_valid)
    print(f"valid_accuracy: {valid_accuracy}")
```


### `Registrable` Class

By using the `Registrable` class, you can devide namespace into each class.
In a following example, `Foo` and `Bar` have different namespaces.

```python
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

if __name__ == "__main__":
    config = {
        "@type": "my_class",
        "foo": {"@type": "baz"},
        "bar": {"@type": "baz"}
    }

    obj = colt.build(config)

    assert isinstance(obj.foo, FooBaz)
    assert isinstance(obj.bar, BarBaz)
```
