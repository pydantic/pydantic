"""
This file contains an initial proposal that can be scrapped and reworked if/when appropriate.
Either way, this test file should probably be removed once the actual FastAPI implementation
is complete and has integration tests with pydantic v2. However, we are including it here for now
to get an early warning if this approach would require modification for compatibility with
any future changes to the JSON schema generation logic, etc.

See the original PR for more details: https://github.com/pydantic/pydantic/pull/5094
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dirty_equals import HasRepr, IsInstance, IsStr

from pydantic import BaseModel, ConfigDict
from pydantic._internal._core_metadata import CoreMetadataHandler
from pydantic._internal._core_utils import CoreSchemaOrField
from pydantic.errors import PydanticInvalidForJsonSchema
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class _ErrorKey(str):
    pass


class FastAPIGenerateJsonSchema(GenerateJsonSchema):
    """
    Idea: This class would be exported from FastAPI, and if users want to modify the way JSON schema is generated
    in FastAPI, they should inherit from it and override it as appropriate.

    In the JSON schema generation logic, FastAPI _could_ also attempt to work with classes that inherit directly from
    GenerateJsonSchema by doing something like:

        if UserGenerateJsonSchema.handle_invalid_for_json_schema is GenerateJsonSchema.handle_invalid_for_json_schema:
            # The method has not been overridden; inherit from FastAPIGenerateJsonSchema
            UserGenerateJsonSchema = type(
                "UserGenerateJsonSchema", (FastAPIGenerateJsonSchema, UserGenerateJsonSchema), {}
            )
        else:
            raise TypeError(f"{UserGenerateJsonSchema.__name__} should inherit from FastAPIGenerateJsonSchema")

    I'm not sure which approach is better.
    """

    def handle_invalid_for_json_schema(self, schema: CoreSchemaOrField, error_info: str) -> JsonSchemaValue:
        # NOTE: I think it may be a good idea to rework this method to either not use CoreMetadataHandler,
        #    and/or to make CoreMetadataHandler a public API.
        if CoreMetadataHandler(schema).metadata.get('pydantic_js_modify_function') is not None:
            # Since there is a json schema modify function, assume that this type is meant to be handled,
            # and the modify function will set all properties as appropriate
            return {}
        else:
            error = PydanticInvalidForJsonSchema(f'Cannot generate a JsonSchema for {error_info}')
            return {_ErrorKey('error'): error}


@dataclass
class ErrorDetails:
    path: list[Any]
    error: PydanticInvalidForJsonSchema


def collect_errors(schema: JsonSchemaValue) -> list[ErrorDetails]:
    errors: list[ErrorDetails] = []

    def _collect_errors(schema: JsonSchemaValue, path: list[Any]) -> None:
        if isinstance(schema, dict):
            for k, v in schema.items():
                if isinstance(k, _ErrorKey):
                    errors.append(ErrorDetails(path, schema[k]))
                _collect_errors(v, list(path) + [k])
        elif isinstance(schema, list):
            for i, v in enumerate(schema):
                _collect_errors(v, list(path) + [i])

    _collect_errors(schema, [])
    return errors


def test_inheritance_detection() -> None:
    class GenerateJsonSchema2(GenerateJsonSchema):
        pass

    assert GenerateJsonSchema2.handle_invalid_for_json_schema is GenerateJsonSchema.handle_invalid_for_json_schema
    # this is just a quick proof of the note above indicating that you can detect whether a specific method
    # is overridden, for the purpose of allowing direct inheritance from GenerateJsonSchema.
    assert (
        FastAPIGenerateJsonSchema.handle_invalid_for_json_schema
        is not GenerateJsonSchema.handle_invalid_for_json_schema
    )


def test_collect_errors() -> None:
    class Car:
        def __init__(self, make: str, model: str, year: int):
            self.make = make
            self.model = model
            self.year = year

    class Model(BaseModel):
        f1: int = 1
        f2: Car

        model_config = ConfigDict(arbitrary_types_allowed=True)

    schema = Model.model_json_schema(schema_generator=FastAPIGenerateJsonSchema)
    assert schema == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'f1': {'type': 'integer', 'default': 1, 'title': 'F1'},
            'f2': {
                'error': HasRepr(IsStr(regex=r'PydanticInvalidForJsonSchema\(.*\)')),
                'title': 'F2',
            },
        },
        'required': ['f2'],
    }

    collected_errors = collect_errors(schema)
    assert collected_errors == [
        ErrorDetails(
            path=['properties', 'f2'],
            error=IsInstance(PydanticInvalidForJsonSchema),
        )
    ]
