import pytest

from colt.jsonschema import JsonSchemaGenerator
from colt.registrable import Registrable


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
                    "additionalProperties": False,
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
                            "additionalProperties": False,
                            "required": ["name"],
                        },
                    },
                    "type": "object",
                    "properties": {
                        "sample": {"$ref": "#/$defs/test_jsonschema__TestJsonSchemaGeneratorWithClass__SampleClass"},
                        "active": {"type": "boolean"},
                    },
                    "additionalProperties": False,
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
    class Foo:
        def __init__(self, name: str, /, *args: int, param: int, **kwargs: str) -> None:
            pass

    @pytest.mark.parametrize(
        "target, expected_schema",
        [
            (
                Foo,
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$defs": {},
                    "title": "TestJsonSchemaGeneratorWithVariableLengthArgs.Foo",
                    "type": "object",
                    "properties": {
                        "param": {"type": "integer"},
                        "*": {
                            "type": "array",
                            "prefixItems": [
                                {"type": "string"},
                            ],
                            "items": {"type": "integer"},
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


class TestJsonSchemaGeneratorWithRegistrable:
    class BaseModel(Registrable):
        pass

    @BaseModel.register("foo")
    class Foo(BaseModel):
        def __init__(self, name: str) -> None:
            self.name = name

    @BaseModel.register("bar")
    class Bar(BaseModel):
        def __init__(self, value: int = 42) -> None:
            self.value = value

    class Composer:
        def __init__(
            self,
            model: "TestJsonSchemaGeneratorWithRegistrable.BaseModel",
            enabled: bool = False,
        ) -> None:
            self.model = model
            self.enabled = enabled

    @pytest.mark.parametrize(
        "target, expected_schema",
        [
            (
                Composer,
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "TestJsonSchemaGeneratorWithRegistrable.Composer",
                    "$defs": {
                        "test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__Foo": {
                            "type": "object",
                            "properties": {
                                "@type": {"const": "foo"},
                                "name": {"type": "string"},
                            },
                            "additionalProperties": False,
                            "required": ["@type", "name"],
                            "title": "TestJsonSchemaGeneratorWithRegistrable.Foo",
                        },
                        "test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__Bar": {
                            "type": "object",
                            "properties": {
                                "@type": {"const": "bar"},
                                "value": {"type": "integer"},
                            },
                            "additionalProperties": False,
                            "required": ["@type"],
                            "title": "TestJsonSchemaGeneratorWithRegistrable.Bar",
                        },
                        "test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__BaseModel": {
                            "title": "TestJsonSchemaGeneratorWithRegistrable.BaseModel",
                            "anyOf": [
                                {"$ref": "#/$defs/test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__Foo"},
                                {"$ref": "#/$defs/test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__Bar"},
                            ],
                        },
                    },
                    "type": "object",
                    "properties": {
                        "model": {"$ref": "#/$defs/test_jsonschema__TestJsonSchemaGeneratorWithRegistrable__BaseModel"},
                        "enabled": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                    "required": ["model"],
                },
            ),
        ],
    )
    @staticmethod
    def test_generate_schema_with_registrable(target, expected_schema):
        generator = JsonSchemaGenerator(strict=True)
        schema = generator(target)
        assert schema == expected_schema
