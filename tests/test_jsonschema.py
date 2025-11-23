import pytest

from colt.jsonschema import JsonSchemaGenerator


class TestJsonSchemaGeneratorWithClass:
    class SampleClass:
        def __init__(self, name: str, age: int = 30):
            self.name = name
            self.age = age

    class NestedClass:
        def __init__(
            self,
            sample: "TestJsonSchemaGeneratorWithClass.SampleClass",
            active: bool = True,
        ):
            self.sample = sample
            self.active = active

    @pytest.mark.parametrize(
        "target, expected_schema",
        [
            (
                SampleClass,
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "TestJsonSchemaGeneratorWithClass.SampleClass",
                    "type": "object",
                    "$defs": {},
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                },
            ),
            (
                NestedClass,
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "TestJsonSchemaGeneratorWithClass.NestedClass",
                    "$defs": {
                        "test_jsonschema__TestJsonSchemaGeneratorWithClass__SampleClass": {
                            "title": "TestJsonSchemaGeneratorWithClass.SampleClass",
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "age": {"type": "integer"},
                            },
                            "required": ["name"],
                        },
                    },
                    "type": "object",
                    "properties": {
                        "sample": {"$ref": "#/$defs/test_jsonschema__TestJsonSchemaGeneratorWithClass__SampleClass"},
                        "active": {"type": "boolean"},
                    },
                    "required": ["sample"],
                },
            ),
        ],
    )
    @staticmethod
    def test_generate_schema_with_class(target, expected_schema):
        generator = JsonSchemaGenerator()
        schema = generator(target)
        assert schema == expected_schema
