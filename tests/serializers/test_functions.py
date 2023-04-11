import json
import sys
from collections import deque
from pathlib import Path

import pytest

from pydantic_core import PydanticOmit, PydanticSerializationError, SchemaError, SchemaSerializer, core_schema


def repr_function(value, _info):
    return repr(value)


@pytest.mark.parametrize(
    'value,expected_python,expected_json',
    [(None, 'None', b'"None"'), (1, '1', b'"1"'), ([1, 2, 3], '[1, 2, 3]', b'"[1, 2, 3]"')],
)
def test_function_general(value, expected_python, expected_json):
    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(repr_function, info_arg=True)
        )
    )
    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json
    assert s.to_python(value, mode='json') == json.loads(expected_json)


def repr_function_no_info(value):
    return repr(value)


@pytest.mark.parametrize(
    'value,expected_python,expected_json',
    [(None, 'None', b'"None"'), (1, '1', b'"1"'), ([1, 2, 3], '[1, 2, 3]', b'"[1, 2, 3]"')],
)
def test_function_no_info(value, expected_python, expected_json):
    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.plain_serializer_function_ser_schema(repr_function_no_info))
    )
    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json
    assert s.to_python(value, mode='json') == json.loads(expected_json)


def test_function_args():
    f_info = None

    def double(value, info):
        nonlocal f_info
        f_info = vars(info)
        return value * 2

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.plain_serializer_function_ser_schema(double, info_arg=True))
    )
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

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(raise_error, info_arg=True)
        )
    )

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
            core_schema.any_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(raise_error, info_arg=True)
            ),
            core_schema.int_schema(),
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
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                append_42, info_arg=True, json_return_type='list'
            )
        )
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
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                append_args, info_arg=True, json_return_type='str'
            )
        )
    )
    assert s.to_python(123) == (
        "123 info=SerializationInfo(include=None, exclude=None, mode='python', by_alias=True, exclude_unset=False, "
        'exclude_defaults=False, exclude_none=False, round_trip=False)'
    )
    assert s.to_python(123, mode='other') == (
        "123 info=SerializationInfo(include=None, exclude=None, mode='other', by_alias=True, exclude_unset=False, "
        'exclude_defaults=False, exclude_none=False, round_trip=False)'
    )
    assert s.to_python(123, include={'x'}) == (
        "123 info=SerializationInfo(include={'x'}, exclude=None, mode='python', by_alias=True, exclude_unset=False, "
        'exclude_defaults=False, exclude_none=False, round_trip=False)'
    )
    assert s.to_python(123, mode='json', exclude={1: {2}}) == (
        "123 info=SerializationInfo(include=None, exclude={1: {2}}, mode='json', by_alias=True, exclude_unset=False, "
        'exclude_defaults=False, exclude_none=False, round_trip=False)'
    )
    assert s.to_json(123) == (
        b'"123 info=SerializationInfo(include=None, exclude=None, mode=\'json\', by_alias=True, exclude_unset=False, '
        b'exclude_defaults=False, exclude_none=False, round_trip=False)"'
    )


def test_invalid_return_type():
    with pytest.raises(SchemaError, match=r'function-plain\.json_return_type\n  Input should be'):
        SchemaSerializer(
            core_schema.any_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda _: 1, info_arg=True, json_return_type='different'
                )
            )
        )


def test_dict_keys():
    def fmt(value, _info):
        return f'<{value}>'

    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.int_schema(serialization=core_schema.plain_serializer_function_ser_schema(fmt, info_arg=True))
        )
    )
    assert s.to_python({1: True}) == {'<1>': True}


def test_function_as_key():
    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.any_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(repr_function, info_arg=True)
            ),
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
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(double, info_arg=True, when_used='json')
        )
    )
    assert s.to_python(4) == 4
    assert s.to_python(4, mode='foobar') == 4

    assert s.to_python(4, mode='json') == 8
    assert s.to_json(4) == b'8'


def test_function_unless_none():
    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                repr_function, info_arg=True, when_used='unless-none'
            )
        )
    )
    assert s.to_python(4) == '4'
    assert s.to_python(None) is None

    assert s.to_python(4, mode='json') == '4'
    assert s.to_python(None, mode='json') is None
    assert s.to_json(4) == b'"4"'
    assert s.to_json(None) == b'null'


def test_wrong_return_type():
    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                repr_function, info_arg=True, json_return_type='int'
            )
        )
    )
    assert s.to_python(123) == '123'
    assert s.to_python(123, mode='json') == '123'

    msg = "Error serializing to JSON: TypeError: 'str' object cannot be interpreted as an integer"
    with pytest.raises(PydanticSerializationError, match=msg):
        s.to_json(123)


def test_wrong_return_type_str():
    def f(value, _):
        if value == 666:
            return value
        else:
            return str(value)

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.plain_serializer_function_ser_schema(
                f, info_arg=True, json_return_type='str_subclass'
            )
        )
    )
    assert s.to_python(123) == '123'
    assert s.to_python(123, mode='json') == '123'
    assert s.to_json(123) == b'"123"'

    assert s.to_python(666) == 666

    with pytest.raises(TypeError, match="^'int' object cannot be converted to 'PyString'$"):
        s.to_python(666, mode='json')

    m = "^Error serializing to JSON: 'int' object cannot be converted to 'PyString'$"
    with pytest.raises(PydanticSerializationError, match=m):
        s.to_json(666)


def test_function_wrap():
    def f(value, serializer, _info):
        return f'result={serializer(len(value))} repr={serializer!r}'

    s = SchemaSerializer(
        core_schema.int_schema(serialization=core_schema.wrap_serializer_function_ser_schema(f, info_arg=True))
    )
    assert s.to_python('foo') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_python('foo', mode='json') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_json('foo') == b'"result=3 repr=SerializationCallable(serializer=int)"'


def test_function_wrap_no_info():
    def f(value, serializer):
        return f'result={serializer(len(value))} repr={serializer!r}'

    s = SchemaSerializer(core_schema.int_schema(serialization=core_schema.wrap_serializer_function_ser_schema(f)))
    assert s.to_python('foo') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_python('foo', mode='json') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_json('foo') == b'"result=3 repr=SerializationCallable(serializer=int)"'


def test_function_wrap_custom_schema():
    def f(value, serializer, _info):
        return f'result={serializer(len(value))} repr={serializer!r}'

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.wrap_serializer_function_ser_schema(
                f, info_arg=True, schema=core_schema.int_schema()
            )
        )
    )
    assert s.to_python('foo') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_python('foo', mode='json') == 'result=3 repr=SerializationCallable(serializer=int)'
    assert s.to_json('foo') == b'"result=3 repr=SerializationCallable(serializer=int)"'


class Foobar:
    def __str__(self):
        return 'foobar!'


def test_function_wrap_fallback():
    def f(value, serializer, _info):
        return f'result={serializer(value)}'

    def fallback(v):
        return f'fallback:{v}'

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.wrap_serializer_function_ser_schema(
                f, info_arg=True, schema=core_schema.any_schema()
            )
        )
    )
    assert s.to_python('foo') == 'result=foo'
    assert s.to_python('foo', mode='json') == 'result=foo'
    assert s.to_json('foo') == b'"result=foo"'

    assert s.to_python(Foobar()) == 'result=foobar!'
    with pytest.raises(PydanticSerializationError, match='Error calling function `f`'):
        assert s.to_python(Foobar(), mode='json') == 'result=foobar!'
    with pytest.raises(PydanticSerializationError, match='Error calling function `f`'):
        assert s.to_json(Foobar()) == b'"result=foobar!"'

    assert s.to_python(Foobar(), fallback=fallback) == 'result=fallback:foobar!'
    assert s.to_python(Foobar(), mode='json', fallback=fallback) == 'result=fallback:foobar!'
    assert s.to_json(Foobar(), fallback=fallback) == b'"result=fallback:foobar!"'


def test_deque():
    def serialize_deque(value, serializer, info: core_schema.SerializationInfo):
        items = []
        for index, item in enumerate(value):
            try:
                v = serializer(item, index)
            except PydanticOmit:
                pass
            else:
                items.append(v)
        if info.mode_is_json():
            return items
        else:
            return deque(items)

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.wrap_serializer_function_ser_schema(
                serialize_deque, info_arg=True, schema=core_schema.any_schema()
            )
        )
    )
    assert s.to_python(deque([1, 2, 3])) == deque([1, 2, 3])
    assert s.to_python(deque([1, 2, 3]), exclude={2}) == deque([1, 2])
    assert s.to_python(deque([1, 2, 3]), include={0}) == deque([1])
    assert s.to_python(deque([1, 2, 3]), mode='json') == [1, 2, 3]
    assert s.to_python(deque([1, 2, 3]), mode='json', exclude={2}) == [1, 2]
    assert s.to_json(deque([1, 2, 3])) == b'[1,2,3]'
    assert s.to_json(deque([1, 2, 3]), exclude={2}) == b'[1,2]'


def test_custom_mapping():
    def serialize_custom_mapping(value, serializer, _info):
        items = {}
        for k, v in value.items():
            try:
                v = serializer(v, k)
            except PydanticOmit:
                pass
            else:
                items[k] = v
        return ' '.join(f'{k}={v}' for k, v in items.items())

    s = SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.wrap_serializer_function_ser_schema(
                serialize_custom_mapping, info_arg=True, schema=core_schema.int_schema()
            )
        )
    )
    assert s.to_python({'a': 1, 'b': 2}) == 'a=1 b=2'
    assert s.to_python({'a': 1, 'b': 2}, exclude={'b'}) == 'a=1'
    assert s.to_python({'a': 1, 'b': 2}, mode='json') == 'a=1 b=2'
    assert s.to_python({'a': 1, 'b': 2}, mode='json', include={'a'}) == 'a=1'
    assert s.to_json({'a': 1, 'b': 2}) == b'"a=1 b=2"'
    assert s.to_json({'a': 1, 'b': 2}, exclude={'b'}) == b'"a=1"'


def test_function_wrap_model():
    calls = 0

    def wrap_function(value, handler, _info):
        nonlocal calls
        calls += 1
        return handler(value)

    class MyModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    s = SchemaSerializer(
        core_schema.model_schema(
            MyModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(core_schema.any_schema()),
                    'b': core_schema.typed_dict_field(core_schema.any_schema()),
                    'c': core_schema.typed_dict_field(core_schema.any_schema(), serialization_exclude=True),
                }
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(wrap_function, info_arg=True),
        )
    )
    m = MyModel(a=1, b=b'foobar', c='excluded')
    assert calls == 0
    assert s.to_python(m) == {'a': 1, 'b': b'foobar'}
    assert calls == 1
    assert s.to_python(m, mode='json') == {'a': 1, 'b': 'foobar'}
    assert calls == 2
    assert s.to_json(m) == b'{"a":1,"b":"foobar"}'
    assert calls == 3

    assert s.to_python(m, exclude={'b'}) == {'a': 1}
    assert calls == 4
    assert s.to_python(m, mode='json', exclude={'b'}) == {'a': 1}
    assert calls == 5
    assert s.to_json(m, exclude={'b'}) == b'{"a":1}'
    assert calls == 6


def test_function_plain_model():
    calls = 0

    def wrap_function(value, _info):
        nonlocal calls
        calls += 1
        return value.__dict__

    class MyModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    s = SchemaSerializer(
        core_schema.model_schema(
            MyModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(core_schema.any_schema()),
                    'b': core_schema.typed_dict_field(core_schema.any_schema()),
                    'c': core_schema.typed_dict_field(core_schema.any_schema(), serialization_exclude=True),
                }
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(wrap_function, info_arg=True),
        )
    )
    m = MyModel(a=1, b=b'foobar', c='not excluded')
    assert calls == 0
    assert s.to_python(m) == {'a': 1, 'b': b'foobar', 'c': 'not excluded'}
    assert calls == 1
    assert s.to_python(m, mode='json') == {'a': 1, 'b': 'foobar', 'c': 'not excluded'}
    assert calls == 2
    assert s.to_json(m) == b'{"a":1,"b":"foobar","c":"not excluded"}'
    assert calls == 3

    assert s.to_python(m, exclude={'b'}) == {'a': 1, 'b': b'foobar', 'c': 'not excluded'}
    assert calls == 4
    assert s.to_python(m, mode='json', exclude={'b'}) == {'a': 1, 'b': 'foobar', 'c': 'not excluded'}
    assert calls == 5
    assert s.to_json(m, exclude={'b'}) == b'{"a":1,"b":"foobar","c":"not excluded"}'
    assert calls == 6


@pytest.mark.skipif(sys.platform == 'win32', reason='Path output different on windows')
def test_wrap_return_type():
    def to_path(value, handler, _info):
        return Path(handler(value)).with_suffix('.new')

    s = SchemaSerializer(
        core_schema.str_schema(
            serialization=core_schema.wrap_serializer_function_ser_schema(
                to_path, info_arg=True, json_return_type='path'
            )
        )
    )
    assert s.to_python('foobar') == Path('foobar.new')
    assert s.to_python('foobar', mode='json') == 'foobar.new'
    assert s.to_json('foobar') == b'"foobar.new"'
