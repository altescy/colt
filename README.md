# 🐎 Colt

[![CI Actions Status](https://github.com/altescy/colt/workflows/CI/badge.svg)](https://github.com/altescy/colt/actions?query=workflow%3ACI)
[![Pulish Actions Status](https://github.com/altescy/colt/workflows/publish/badge.svg)](https://github.com/altescy/colt/actions?query=workflow%3Apublish)
[![Python version](https://img.shields.io/pypi/pyversions/colt)](https://github.com/altescy/colt)
[![pypi version](https://img.shields.io/pypi/v/colt)](https://pypi.org/project/colt/)
[![license](https://img.shields.io/github/license/altescy/colt)](https://github.com/altescy/colt/blob/master/LICENSE)

Effortlessly configure and construct Python objects with `colt`, a lightweight library inspired by [AllenNLP](https://github.com/allenai/allennlp) and [Tango](https://github.com/allenai/tango)

## Quick Links

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Influences](#influences)
- [kaggle Titanic Example](https://github.com/altescy/colt/tree/master/examples/titanic)

## Introduction

`colt` is a lightweight configuration utility for Python objects, allowing you to manage complex configurations for your projects easily.
Written solely using the Python standard library, `colt` can construct class objects from JSON-convertible dictionaries, making it simple to manage your settings using JSON or YAML files. The library is particularly suitable for the [dependency injection](https://en.wikipedia.org/wiki/Dependency_injection) design pattern.

Some key features of colt include:

- No external dependencies, as it is built using the Python standard library.
- Construct class objects from JSON-convertible dictionaries.
- Manage complex configurations using JSON or YAML files.
- Well-suited for dependency injection design patterns.

Inspired by [AllenNLP](https://github.com/allenai/allennlp) and [Tango](https://github.com/allenai/tango), `colt` aims to offer similar functionality while focusing on a more lightweight and user-friendly design.

### Differences between `colt` and AllenNLP/Tango

While both AllenNLP and Tango construct objects based on the class signature, colt focuses on building objects from the type specified in the configuration. Although colt is aware of the class signature, it primarily uses it for validation when passing objects created from the configuration.

This means that with colt, you don't necessarily need to have the target class available for configuration. As a result, you can conveniently build objects using the colt.build method without requiring the specific class to be present. This distinction makes colt more flexible and easier to work with in various scenarios.

## Installation

To install colt, simply run the following command:

```shell
pip install colt
```

## Usage

### Basic Example

Here is a basic example of how to use `colt` to create class objects from a configuration dictionary:

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

### Functionality

#### Guiding Object Construction with a Target Class

You can guide the object construction process in `colt` by passing the desired class as the second argument to the `colt.build` method.
Here's an example demonstrating this functionality:

```python
@colt.register("foo")
class Foo:
    def __init__(self, x: str) -> None:
        self.x = x

config = {"x": "abc"}

# Pass the desired class as the second argument
obj = colt.build(config, Foo)

assert isinstance(obj, Foo)
assert obj.x == "abc"
```

By providing the target class to `colt.build`, you can ensure the constructed object is of the desired type while still using the configuration for parameter values.

#### `Registrable` class

`colt` provides the Registrable class, which allows you to divide the namespace for each class.
This can be particularly useful when working with larger projects or when you need to manage multiple classes with the same name but different functionality.

Here is an example of how to use the `Registrable` class to manage different namespaces for `Foo` and `Bar`:

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

#### `Lazy` class

`colt` offers a `Lazy` class for deferring object creation until needed, which can be useful in cases where constructing an object is computationally expensive or should be delayed until certain conditions are met.

Here's a concise example demonstrating the `Lazy` class usage with `colt`:

```python
import dataclasses
import colt
from colt import Lazy

@dataclasses.dataclass
class Foo:
    x: str
    y: int

@dataclasses.dataclass
class Bar:
    foo: Lazy[Foo]

bar = colt.build({"foo": {"x": "hello"}}, Bar)

# Additional parameters can be passed when calling the construct() method
foo = bar.foo.construct(y=10)
```

In this example, `Bar` contains a `Lazy` instance of `Foo`, which will only be constructed when `construct()` is called.
When calling `construct()`, you can pass additional parameters required for the object's construction.
This approach allows you to control when an object is created, optimizing resource usage and computations while providing flexibility in passing parameters.

### Advanced Examples

#### scikit-learn Configuration

Here's an example of how to use `colt` to configure a [scikit-learn](https://scikit-learn.org/) model:

```python
import colt

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    config = {
        # these types are imported automatically if type name is not registerd
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

In this example, `colt` is used to configure a `VotingClassifier` from scikit-learn, combining a `RandomForestClassifier` and an `SVC`.
The colt configuration dictionary makes it easy to manage the settings of these classifiers and modify them as needed.

## Influences

`colt` is heavily influenced by the following projects:

- [AllenNLP](https://github.com/allenai/allennlp): A popular natural language processing library, which provides a powerful configuration system for managing complex experiments.
- [Tango](https://github.com/allenai/tango): A lightweight and flexible library for running machine learning experiments, designed to work well with AllenNLP and other libraries.

These projects have demonstrated the value of a robust configuration system for managing machine learning experiments and inspired the design of `colt`.
