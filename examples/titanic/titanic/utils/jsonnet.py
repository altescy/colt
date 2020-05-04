import typing as tp

import json
import os

from _jsonnet import evaluate_file


def _is_encodable(value: str) -> bool:
    return (value == "") or (value.encode("utf-8", "ignore") != b"")


def _environment_variables() -> tp.Dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items() if _is_encodable(value)
    }


def load_jsonnet(path: str) -> tp.Dict[str, tp.Any]:
    ext_vars = _environment_variables()
    jsondict = json.loads(evaluate_file(str(path), ext_vars=ext_vars))
    return tp.cast(tp.Dict[str, tp.Any], jsondict)
