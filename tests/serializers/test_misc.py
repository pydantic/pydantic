import pytest

from pydantic_core import SchemaError, core_schema, validate_core_schema


@pytest.mark.parametrize(
    'ser_schema,msg',
    [
        ({'invalid': 'schema'}, "Unable to extract tag using discriminator 'type'"),
        ({'type': 'unknown'}, "Input tag 'unknown' found using 'type' does not match any of the expected tags:"),
    ],
)
def test_invalid_ser_schema(ser_schema, msg):
    with pytest.raises(SchemaError, match=msg):
        validate_core_schema(core_schema.any_schema(serialization=ser_schema))
