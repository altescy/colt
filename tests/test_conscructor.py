import colt


@colt.register("plugh", constructor="plugh_constructor")
class Plugh:
    def __init__(self, x: str, y: str) -> None:
        self.x = x
        self.y = y

    @classmethod
    def plugh_constructor(cls, x: str, y: str) -> "Plugh":
        x += "_x"
        y += "_y"
        return cls(x, y)


def test_colt_constructor():
    config = {"@type": "plugh", "*": ["plugh"], "y": "plugh"}

    obj = colt.build(config)

    assert obj.x == "plugh_x"
    assert obj.y == "plugh_y"
