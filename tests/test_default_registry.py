import colt


def test_colt_builtintypes() -> None:
    config = [{"@type": "tuple", "*": [[1, 2, 3]]}, {"@type": "range", "*": [0, 10, 2]}]

    obj = colt.build(config)

    assert isinstance(obj[0], tuple)
    assert isinstance(obj[1], range)
