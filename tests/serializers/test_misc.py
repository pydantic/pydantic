import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema


@pytest.mark.parametrize(
    'ser_schema,msg',
    [
        ({'invalid': 'schema'}, "Unable to extract tag using discriminator 'type'"),
        ({'type': 'unknown'}, "Input tag 'unknown' found using 'type' does not match any of the expected tags:"),
    ],
)
def test_invalid_ser_schema(ser_schema, msg):
    with pytest.raises(SchemaError, match=msg):
        SchemaSerializer(core_schema.any_schema(serialization=ser_schema))
