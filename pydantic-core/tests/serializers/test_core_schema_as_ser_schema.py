"""Tests for arbitrary core schemas being used as the `serialization` schema."""

from typing import Any

import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema

from ..conftest import plain_repr


@pytest.mark.parametrize(
    ['ser_schema', 'value', 'expected_python', 'expected_json'],
    [
        # equivalent to `simple_ser_schema('list')` (i.e. it must still work):
        (core_schema.simple_ser_schema('list'), [1, 'a'], [1, 'a'], b'[1,"a"]'),
        (core_schema.list_schema(core_schema.int_schema()), [1, 2], [1, 2], b'[1,2]'),
        (
            core_schema.tuple_schema([core_schema.int_schema(), core_schema.str_schema()]),
            (1, 'a'),
            (1, 'a'),
            b'[1,"a"]',
        ),
        (
            core_schema.dict_schema(core_schema.str_schema(), core_schema.int_schema()),
            {'a': 1},
            {'a': 1},
            b'{"a":1}',
        ),
        (
            core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(core_schema.int_schema())}),
            {'a': 1, 'b': 2},
            {'a': 1},
            b'{"a":1}',
        ),
        (
            core_schema.definitions_schema(
                core_schema.definition_reference_schema('list_of_int'),
                [core_schema.list_schema(core_schema.int_schema(), ref='list_of_int')],
            ),
            [1, 2],
            [1, 2],
            b'[1,2]',
        ),
        # `'function-before'`/`'function-after'` core schemas serialize using the inner schema:
        (
            core_schema.no_info_after_validator_function(lambda v: v, core_schema.int_schema()),
            1,
            1,
            b'1',
        ),
    ],
)
def test_core_schema_as_ser_schema(ser_schema: Any, value: Any, expected_python: Any, expected_json: bytes) -> None:
    s = SchemaSerializer(core_schema.any_schema(serialization=ser_schema))

    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json


def test_core_schema_as_ser_schema_expected_type() -> None:
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.list_schema(core_schema.int_schema())))

    with pytest.warns(UserWarning, match=r'Expected `int` - serialized value may not be as expected'):
        assert s.to_python(['a']) == ['a']


def test_core_schema_as_ser_schema_nested_serialization() -> None:
    """The `serialization` schema of the core schema used as a `serialization` schema is taken into account."""
    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.int_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(lambda v: v * 2),
            ),
        )
    )

    assert s.to_python(3) == 6
    assert s.to_json(3) == b'6'


def test_core_schema_as_ser_schema_unknown_type() -> None:
    with pytest.raises(SchemaError, match=r'Unknown serialization schema type: `unknown`'):
        SchemaSerializer(core_schema.any_schema(serialization={'type': 'unknown'}))  # pyright: ignore[reportArgumentType]


def test_model_schema_as_ser_schema_polymorphic() -> None:
    class Model:
        __pydantic_complete__ = True

    class SubModel(Model):
        pass

    model_schema = core_schema.model_schema(
        Model,
        schema=core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.int_schema())}),
        config=core_schema.CoreConfig(polymorphic_serialization=True),
    )
    Model.__pydantic_serializer__ = SchemaSerializer(model_schema)  # pyright: ignore[reportAttributeAccessIssue]

    sub_model_schema = core_schema.model_schema(
        SubModel,
        schema=core_schema.model_fields_schema(
            {
                'x': core_schema.model_field(core_schema.int_schema()),
                'y': core_schema.model_field(core_schema.int_schema()),
            }
        ),
    )
    SubModel.__pydantic_serializer__ = SchemaSerializer(sub_model_schema)  # pyright: ignore[reportAttributeAccessIssue]

    s = SchemaSerializer(core_schema.any_schema(serialization=model_schema))
    # Using the model schema as a serialization schema behaves the same as using it as the main schema
    # (in this case, the prebuilt serializer of `Model` is used, wrapped in a polymorphism trampoline):
    assert plain_repr(s) == plain_repr(SchemaSerializer(model_schema))
    assert plain_repr(s).startswith(
        'SchemaSerializer(serializer=PolymorphismTrampoline(PolymorphismTrampoline{class:Py(0x'
    )
    assert 'serializer:Prebuilt(PrebuiltSerializer{' in plain_repr(s)

    sub_model = SubModel()
    sub_model.__dict__ = {'x': 1, 'y': 2}
    assert s.to_python(sub_model) == {'x': 1, 'y': 2}
    assert s.to_json(sub_model) == b'{"x":1,"y":2}'
