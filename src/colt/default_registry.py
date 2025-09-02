from colt.registrable import Registrable


class DefaultRegistry(Registrable):
    """default type store"""


DefaultRegistry.register("bool")(bool)
DefaultRegistry.register("byte")(bytes)
DefaultRegistry.register("bytearray")(bytearray)
DefaultRegistry.register("memoryview")(memoryview)
DefaultRegistry.register("complex")(complex)
DefaultRegistry.register("dict")(dict)
DefaultRegistry.register("float")(float)
DefaultRegistry.register("frozenset")(frozenset)
DefaultRegistry.register("int")(int)
DefaultRegistry.register("list")(list)
DefaultRegistry.register("range")(range)
DefaultRegistry.register("set")(set)
DefaultRegistry.register("str")(str)
DefaultRegistry.register("tuple")(tuple)
