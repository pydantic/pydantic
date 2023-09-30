from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic_core import core_schema as cs

N = 5  # arbitrary number that takes ~0.05s per run


class MyModel:
    # __slots__ is not required, but it avoids __pydantic_fields_set__ falling into __dict__
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def schema_using_defs() -> cs.CoreSchema:
    definitions: list[cs.CoreSchema] = [
        {'type': 'int', 'ref': 'int'},
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    str(c): {'type': 'model-field', 'schema': {'type': 'definition-ref', 'schema_ref': 'int'}}
                    for c in range(N)
                },
            },
            'ref': f'model_{N}',
        },
    ]
    level = N
    for level in reversed(range(N)):
        definitions.append(
            {
                'type': 'model',
                'cls': MyModel,
                'schema': {
                    'type': 'model-fields',
                    'fields': {
                        str(c): {
                            'type': 'model-field',
                            'schema': {'type': 'definition-ref', 'schema_ref': f'model_{level+1}'},
                        }
                        for c in range(N)
                    },
                },
                'ref': f'model_{level}',
            }
        )
    return {
        'type': 'definitions',
        'definitions': definitions,
        'schema': {'type': 'definition-ref', 'schema_ref': 'model_0'},
    }


def inlined_schema() -> cs.CoreSchema:
    level = N
    schema: cs.CoreSchema = {
        'type': 'model',
        'cls': MyModel,
        'schema': {
            'type': 'model-fields',
            'fields': {str(c): {'type': 'model-field', 'schema': {'type': 'int'}} for c in range(N)},
        },
        'ref': f'model_{N}',
    }
    for level in reversed(range(N)):
        schema = {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'model-fields',
                'fields': {str(c): {'type': 'model-field', 'schema': schema} for c in range(N)},
            },
            'ref': f'model_{level}',
        }
    return schema


def input_data_valid(levels: int = N) -> Any:
    data = {str(c): 1 for c in range(N)}
    for _ in range(levels):
        data = {str(c): data for c in range(N)}
    return data


if __name__ == '__main__':
    from pydantic_core import SchemaValidator

    SchemaValidator(schema_using_defs()).validate_python(input_data_valid())
    SchemaValidator(inlined_schema()).validate_python(input_data_valid())
