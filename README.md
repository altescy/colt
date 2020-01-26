colt
===

[![Actions Status](https://github.com/altescy/colt/workflows/build/badge.svg)](https://github.com/altescy/colt)
[![Python version](https://img.shields.io/pypi/pyversions/colt)](https://github.com/altescy/colt)
[![pypi version](https://img.shields.io/pypi/v/colt)](https://pypi.org/project/colt/)
[![license](https://img.shields.io/github/license/altescy/colt)](https://github.com/altescy/colt/blob/master/LICENSE)

## Introduction

`colt` is a configuration utility for Python object.
`colt` constructs Python object from configuration dict which is convertable into JSON.


## Installation

```
pip install colt
```

## Example

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
        "@type": "bar",  # specify type-name with `@type`
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
