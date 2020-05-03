colt
===

[![Actions Status](https://github.com/altescy/colt/workflows/build/badge.svg)](https://github.com/altescy/colt)
[![Python version](https://img.shields.io/pypi/pyversions/colt)](https://github.com/altescy/colt)
[![pypi version](https://img.shields.io/pypi/v/colt)](https://pypi.org/project/colt/)
[![license](https://img.shields.io/github/license/altescy/colt)](https://github.com/altescy/colt/blob/master/LICENSE)

## Introduction

`colt` is a configuration utility for Python objects.
`colt` constructs Python objects from a configuration dict which is convertable into JSON.
(Inspired by [AllenNLP](https://github.com/allenai/allennlp))


## Installation

```
pip install colt
```

## Example

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
