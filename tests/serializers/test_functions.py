import json

import pytest

from pydantic_core import PydanticSerializationError, SchemaError, SchemaSerializer, core_schema


@pytest.mark.parametrize(
    'value,expected_python,expected_json',
    [(None, 'None', b'"None"'), (1, '1', b'"1"'), ([1, 2, 3], '[1, 2, 3]', b'"[1, 2, 3]"')],
)
def test_function(value, expected_python, expected_json):
    def repr_function(value, _info):
        return repr(value)

    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.function_ser_schema(repr_function)))
    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json
    assert s.to_python(value, mode='json') == json.loads(expected_json)


def test_function_args():
    f_info = None

    def double(value, info):
        nonlocal f_info
        f_info = vars(info)
        return value * 2

    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.function_ser_schema(double)))
    assert s.to_python(4) == 8
    # insert_assert(f_info)
    assert f_info == {
        'mode': 'python',
        'by_alias': True,
        'exclude_unset': False,
        'exclude_defaults': False,
        'exclude_none': False,
        'round_trip': False,
    }
    assert s.to_python('x') == 'xx'

    assert s.to_python(4, mode='foobar') == 8
    # insert_assert(f_info)
    assert f_info == {
        'mode': 'foobar',
        'by_alias': True,
        'exclude_unset': False,
        'exclude_defaults': False,
        'exclude_none': False,
        'round_trip': False,
    }

    assert s.to_json(42) == b'84'
    # insert_assert(f_info)
    assert f_info == {
        'mode': 'json',
        'by_alias': True,
        'exclude_unset': False,
        'exclude_defaults': False,
        'exclude_none': False,
        'round_trip': False,
    }

    assert s.to_python(7, mode='json', by_alias=False, exclude_unset=True) == 14
    # insert_assert(f_info)
    assert f_info == {
        'mode': 'json',
        'by_alias': False,
        'exclude_unset': True,
        'exclude_defaults': False,
        'exclude_none': False,
        'round_trip': False,
    }

    assert s.to_python(1, include={1, 2, 3}, exclude={'foo': {'bar'}}) == 2
    # insert_assert(f_info)
    assert f_info == {
        'include': {3, 2, 1},
        'exclude': {'foo': {'bar'}},
        'mode': 'python',
        'by_alias': True,
        'exclude_unset': False,
        'exclude_defaults': False,
        'exclude_none': False,
        'round_trip': False,
    }


def test_function_error():
    def raise_error(value, _info):
        raise TypeError('foo')

    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.function_ser_schema(raise_error)))

    msg = 'Error calling function `raise_error`: TypeError: foo$'
    with pytest.raises(PydanticSerializationError, match=msg) as exc_info:
        s.to_python('abc')
    assert isinstance(exc_info.value.__cause__, TypeError)

    with pytest.raises(PydanticSerializationError, match=msg) as exc_info:
        s.to_python('abc', mode='json')
    assert isinstance(exc_info.value.__cause__, TypeError)

    with pytest.raises(PydanticSerializationError, match=msg):
        s.to_json('foo')


def test_function_error_keys():
    def raise_error(value, _info):
        raise TypeError('foo')

    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.any_schema(serialization=core_schema.function_ser_schema(raise_error)), core_schema.int_schema()
        )
    )

    msg = 'Error calling function `raise_error`: TypeError: foo$'
    with pytest.raises(PydanticSerializationError, match=msg) as exc_info:
        s.to_python({'abc': 1})
    assert isinstance(exc_info.value.__cause__, TypeError)

    with pytest.raises(PydanticSerializationError, match=msg) as exc_info:
        s.to_python({'abc': 1}, mode='json')
    assert isinstance(exc_info.value.__cause__, TypeError)

    with pytest.raises(PydanticSerializationError, match=msg):
        s.to_json({'abc': 1})


def test_function_known_type():
    def append_42(value, _info):
        if isinstance(value, list):
            value.append(42)
        return value

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.function_ser_schema(append_42, json_return_type='list'))
    )
    assert s.to_python([1, 2, 3]) == [1, 2, 3, 42]
    assert s.to_python([1, 2, 3], mode='json') == [1, 2, 3, 42]
    assert s.to_json([1, 2, 3]) == b'[1,2,3,42]'

    assert s.to_python('abc') == 'abc'

    with pytest.raises(TypeError, match="'str' object cannot be converted to 'PyList'"):
        s.to_python('abc', mode='json')

    msg = "Error serializing to JSON: 'str' object cannot be converted to 'PyList'"
    with pytest.raises(PydanticSerializationError, match=msg):
        s.to_json('abc')


def test_function_args_str():
    def append_args(value, info):
        return f'{value} info={info}'

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.function_ser_schema(append_args, json_return_type='str'))
    )
    assert s.to_python(123) == (
        "123 info=SerializationInfo(include=None, exclude=None, mode='python', by_alias=True, exclude_unset=False, "
        "exclude_defaults=False, exclude_none=False, round_trip=False)"
    )
    assert s.to_python(123, mode='other') == (
        "123 info=SerializationInfo(include=None, exclude=None, mode='other', by_alias=True, exclude_unset=False, "
        "exclude_defaults=False, exclude_none=False, round_trip=False)"
    )
    assert s.to_python(123, include={'x'}) == (
        "123 info=SerializationInfo(include={'x'}, exclude=None, mode='python', by_alias=True, exclude_unset=False, "
        "exclude_defaults=False, exclude_none=False, round_trip=False)"
    )
    assert s.to_python(123, mode='json', exclude={1: {2}}) == (
        "123 info=SerializationInfo(include=None, exclude={1: {2}}, mode='json', by_alias=True, exclude_unset=False, "
        "exclude_defaults=False, exclude_none=False, round_trip=False)"
    )
    assert s.to_json(123) == (
        b'"123 info=SerializationInfo(include=None, exclude=None, mode=\'json\', by_alias=True, exclude_unset=False, '
        b'exclude_defaults=False, exclude_none=False, round_trip=False)"'
    )


def test_invalid_return_type():
    with pytest.raises(SchemaError, match='function -> json_return_type\n  Input should be'):
        SchemaSerializer(
            core_schema.any_schema(
                serialization=core_schema.function_ser_schema(lambda _: 1, json_return_type='different')
            )
        )


def test_dict_keys():
    def fmt(value, _info):
        return f'<{value}>'

    s = SchemaSerializer(
        core_schema.dict_schema(core_schema.int_schema(serialization=core_schema.function_ser_schema(fmt)))
    )
    assert s.to_python({1: True}) == {'<1>': True}


def test_function_as_key():
    def repr_function(value, _info):
        return repr(value)

    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.any_schema(serialization=core_schema.function_ser_schema(repr_function)),
            core_schema.any_schema(),
        )
    )
    assert s.to_python({123: 4}) == {'123': 4}
    assert s.to_python({123: 4}, mode='json') == {'123': 4}
    assert s.to_json({123: 4}) == b'{"123":4}'


def test_function_only_json():
    def double(value, _):
        return value * 2

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.function_ser_schema(double, when_used='json'))
    )
    assert s.to_python(4) == 4
    assert s.to_python(4, mode='foobar') == 4

    assert s.to_python(4, mode='json') == 8
    assert s.to_json(4) == b'8'


def test_function_unless_none():
    def to_repr(value, _):
        return repr(value)

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.function_ser_schema(to_repr, when_used='unless-none'))
    )
    assert s.to_python(4) == '4'
    assert s.to_python(None) is None

    assert s.to_python(4, mode='json') == '4'
    assert s.to_python(None, mode='json') is None
    assert s.to_json(4) == b'"4"'
    assert s.to_json(None) == b'null'
