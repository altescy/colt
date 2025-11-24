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
        generator = JsonSchemaGenerator(strict=True)
        schema = generator(target)
        assert schema == expected_schema


class TestJsonSchemaGeneratorWithVariableLengthArgs:
    @staticmethod
    def sample_function(name: str, /, *args: int, param: int, **kwargs: str) -> None:
        pass

    @pytest.mark.parametrize(
        "target, expected_schema",
        [
            (
                sample_function,
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$defs": {},
                    "type": "object",
                    "properties": {
                        "param": {"type": "integer"},
                        "*": {
                            "type": "array",
                            "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                        },
                    },
                    "additionalProperties": {"type": "string"},
                    "required": ["param"],
                },
            ),
        ],
    )
    @staticmethod
    def test_generate_schema_with_variable_length_args(target, expected_schema):
        generator = JsonSchemaGenerator(strict=True)
        schema = generator(target)
        assert schema == expected_schema
