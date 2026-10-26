import pytest

from pydantic_core import (
    MISSING,
    PydanticSerializationError,
    PydanticSerializationUnexpectedValue,
    SchemaSerializer,
    core_schema,
)


def test_missing_sentinel_no_inner_schema() -> None:
    s = SchemaSerializer(core_schema.missing_sentinel_schema())

    assert s.to_python(MISSING) is MISSING

    with pytest.raises(PydanticSerializationUnexpectedValue, match="Expected 'MISSING' sentinel"):
        s.to_python(1)

    with pytest.raises(ValueError, match="'MISSING' can't be serialized to JSON"):
        s.to_json(MISSING)


def test_missing_sentinel_inner_schema() -> None:
    s = SchemaSerializer(core_schema.missing_sentinel_schema(core_schema.int_schema()))

    assert s.to_python(MISSING) is MISSING
    assert s.to_python(1) == 1
    assert s.to_python(1, mode='json') == 1
    assert s.to_json(1) == b'1'

    with pytest.raises(ValueError, match="'MISSING' can't be serialized to JSON"):
        s.to_json(MISSING)


def test_missing_sentinel_inner_schema_serialization_warning() -> None:
    s = SchemaSerializer(core_schema.missing_sentinel_schema(core_schema.int_schema()))

    with pytest.warns(UserWarning, match='Expected `int`'):
        s.to_python('hello')


def test_missing_sentinel_dict_key() -> None:
    s = SchemaSerializer(
        core_schema.dict_schema(
            keys_schema=core_schema.missing_sentinel_schema(core_schema.int_schema()),
            values_schema=core_schema.int_schema(),
        )
    )

    assert s.to_python({1: 2}, mode='json') == {'1': 2}
    assert s.to_json({1: 2}) == b'{"1":2}'

    with pytest.raises(PydanticSerializationError, match='Unable to serialize unknown type'):
        s.to_json({MISSING: 2})


def test_missing_sentinel_typed_dict_field_omitted() -> None:
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'f': core_schema.typed_dict_field(
                    core_schema.with_default_schema(
                        core_schema.missing_sentinel_schema(core_schema.int_schema()), default=MISSING
                    )
                ),
                'g': core_schema.typed_dict_field(core_schema.int_schema()),
            }
        )
    )

    assert s.to_python({'f': MISSING, 'g': 1}) == {'g': 1}
    assert s.to_python({'f': 1, 'g': 1}) == {'f': 1, 'g': 1}
    assert s.to_json({'f': MISSING, 'g': 1}) == b'{"g":1}'
