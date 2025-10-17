import json
import pickle
from datetime import timedelta

import pytest

from pydantic_core import core_schema
from pydantic_core._pydantic_core import SchemaSerializer


def repr_function(value, _info):
    return repr(value)


def test_basic_schema_serializer():
    s = SchemaSerializer(core_schema.dict_schema())
    s = pickle.loads(pickle.dumps(s))
    assert s.to_python({'a': 1, b'b': 2, 33: 3}) == {'a': 1, b'b': 2, 33: 3}
    assert s.to_python({'a': 1, b'b': 2, 33: 3, True: 4}, mode='json') == {'a': 1, 'b': 2, '33': 3, 'true': 4}
    assert s.to_json({'a': 1, b'b': 2, 33: 3, True: 4}) == b'{"a":1,"b":2,"33":3,"true":4}'

    assert s.to_python({(1, 2): 3}) == {(1, 2): 3}
    assert s.to_python({(1, 2): 3}, mode='json') == {'1,2': 3}
    assert s.to_json({(1, 2): 3}) == b'{"1,2":3}'


@pytest.mark.parametrize(
    'value,expected_python,expected_json',
    [(None, 'None', b'"None"'), (1, '1', b'"1"'), ([1, 2, 3], '[1, 2, 3]', b'"[1, 2, 3]"')],
)
def test_schema_serializer_capturing_function(value, expected_python, expected_json):
    # Test a SchemaSerializer that captures a function.
    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(repr_function, info_arg=True)
        )
    )
    s = pickle.loads(pickle.dumps(s))
    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json
    assert s.to_python(value, mode='json') == json.loads(expected_json)


def test_schema_serializer_containing_config():
    s = SchemaSerializer(core_schema.timedelta_schema(), config={'ser_json_timedelta': 'float'})
    s = pickle.loads(pickle.dumps(s))

    assert s.to_python(timedelta(seconds=4, microseconds=500_000)) == timedelta(seconds=4, microseconds=500_000)
    assert s.to_python(timedelta(seconds=4, microseconds=500_000), mode='json') == 4.5
    assert s.to_json(timedelta(seconds=4, microseconds=500_000)) == b'4.5'


# Should be defined at the module level for pickling to work:
class Model:
    __pydantic_serializer__: SchemaSerializer
    __pydantic_complete__ = True


def test_schema_serializer_not_reused_when_unpickling() -> None:
    s = SchemaSerializer(
        core_schema.model_schema(
            cls=Model,
            schema=core_schema.model_fields_schema(fields={}, model_name='Model'),
            config={'title': 'Model'},
            ref='Model:123',
        )
    )

    Model.__pydantic_serializer__ = s
    assert 'Prebuilt' not in str(Model.__pydantic_serializer__)

    reconstructed = pickle.loads(pickle.dumps(Model.__pydantic_serializer__))
    assert 'Prebuilt' not in str(reconstructed)
