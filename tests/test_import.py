import colt


def test_colt_import():
    config = {"@type": "datetime.date", "year": 2020, "month": 1, "day": 1}

    obj = colt.build(config)

    assert obj.year == 2020
