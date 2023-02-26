import dataclasses
import json
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import ClassVar

import pytest
from dirty_equals import IsList

from pydantic_core import PydanticSerializationError, SchemaSerializer, core_schema, to_json

from ..conftest import plain_repr
from .test_list_tuple import as_list, as_tuple


@pytest.fixture(scope='module')
def any_serializer():
    return SchemaSerializer(core_schema.any_schema())


def test_repr(any_serializer):
    assert plain_repr(any_serializer) == 'SchemaSerializer(serializer=Any(AnySerializer),slots=[])'


@dataclasses.dataclass(frozen=True)
class MyDataclass:
    class_var: ClassVar[int] = 1
    a: int
    b: str
    frog: dataclasses.InitVar[int]


class MyModel:
    __pydantic_validator__ = 42

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.mark.parametrize('value', [None, 1, 1.0, True, 'foo', [1, 2, 3], {'a': 1, 'b': 2}])
def test_any_json_round_trip(any_serializer, value):
    assert any_serializer.to_python(value) == value
    assert json.loads(any_serializer.to_json(value)) == value
    assert any_serializer.to_python(value, mode='json') == value


@pytest.mark.parametrize(
    'input_value,expected_plain,expected_json_obj',
    [
        (MyDataclass(1, 'foo', 3), {'a': 1, 'b': 'foo'}, {'a': 1, 'b': 'foo'}),
        (MyModel(a=1, b='foo'), {'a': 1, 'b': 'foo'}, {'a': 1, 'b': 'foo'}),
        ({1, 2, 3}, {1, 2, 3}, IsList(1, 2, 3, check_order=False)),
        ({1, '2', b'3'}, {1, '2', b'3'}, IsList(1, '2', '3', check_order=False)),
    ],
)
def test_any_python(any_serializer, input_value, expected_plain, expected_json_obj):
    assert any_serializer.to_python(input_value) == expected_plain
    assert any_serializer.to_python(input_value, mode='json') == expected_json_obj
    assert json.loads(any_serializer.to_json(input_value)) == expected_json_obj


def test_set_member_db(any_serializer):
    input_value = {MyDataclass(1, 'a', 2), MyDataclass(2, 'b', 2)}
    expected_json_obj = IsList({'a': 1, 'b': 'a'}, {'a': 2, 'b': 'b'}, check_order=False)
    assert any_serializer.to_python(input_value, mode='json') == expected_json_obj
    assert json.loads(any_serializer.to_json(input_value)) == expected_json_obj
    with pytest.raises(TypeError, match="unhashable type: 'dict'"):
        any_serializer.to_python(input_value)


@pytest.mark.parametrize(
    'value,expected_json',
    [
        (None, b'null'),
        (1, b'1'),
        (Decimal('1.123'), b'"1.123"'),
        (b'foobar', b'"foobar"'),
        (bytearray(b'foobar'), b'"foobar"'),
        ((1, 2, 3), b'[1,2,3]'),
        ({1: 2, 'a': 4}, b'{"1":2,"a":4}'),
        ({(1, 'a', 2): 3}, b'{"1,a,2":3}'),
        ({(1,): 3}, b'{"1":3}'),
        (datetime(2022, 12, 3, 12, 30, 45), b'"2022-12-03T12:30:45"'),
        (datetime(2032, 1, 1, 1, 1), b'"2032-01-01T01:01:00"'),
        (date(2022, 12, 3), b'"2022-12-03"'),
        (time(12, 30, 45), b'"12:30:45"'),
        (timedelta(hours=2), b'"PT7200S"'),
        (MyDataclass(1, 'foo', 2), b'{"a":1,"b":"foo"}'),
        (MyModel(a=1, b='foo'), b'{"a":1,"b":"foo"}'),
        ([MyDataclass(1, 'a', 2), MyModel(a=2, b='b')], b'[{"a":1,"b":"a"},{"a":2,"b":"b"}]'),
    ],
)
def test_any_json(any_serializer, value, expected_json):
    assert any_serializer.to_json(value) == expected_json
    assert any_serializer.to_python(value, mode='json') == json.loads(expected_json)


def test_other_type():
    """Types with no serializer, fall back to any serializer"""
    v = SchemaSerializer(core_schema.is_instance_schema(int))
    assert plain_repr(v) == 'SchemaSerializer(serializer=Any(AnySerializer),slots=[])'
    assert v.to_json('foobar') == b'"foobar"'


@pytest.mark.parametrize('value', [b'\x81', bytearray(b'\x81')])
def test_any_json_decode_error(any_serializer, value):
    assert any_serializer.to_python(value) == value

    msg = 'Error serializing to JSON: invalid utf-8 sequence of 1 bytes from index 0'
    with pytest.raises(PydanticSerializationError, match=msg):
        any_serializer.to_json(value)

    with pytest.raises(ValueError):
        any_serializer.to_python(value, mode='json')


def test_any_with_date_serializer():
    s = SchemaSerializer(core_schema.any_schema(serialization={'type': 'date'}))
    assert s.to_python(date(2022, 12, 3)) == date(2022, 12, 3)
    assert s.to_python(date(2022, 12, 3), mode='json') == '2022-12-03'
    assert s.to_json(date(2022, 12, 3)) == b'"2022-12-03"'

    with pytest.warns(UserWarning) as warning_info:
        assert s.to_python(b'bang', mode='json') == 'bang'

    assert [w.message.args[0] for w in warning_info.list] == [
        'Pydantic serializer warnings:\n  Expected `date` but got `bytes` - serialized value may not be as expected'
    ]


def test_any_with_timedelta_serializer():
    s = SchemaSerializer(core_schema.any_schema(serialization={'type': 'timedelta'}))
    assert s.to_python(timedelta(hours=2)) == timedelta(hours=2)
    assert s.to_python(timedelta(hours=2), mode='json') == 'PT7200S'
    assert s.to_json(timedelta(hours=2)) == b'"PT7200S"'

    with pytest.warns(UserWarning) as warning_info:
        assert s.to_python(b'bang', mode='json') == 'bang'

    assert [w.message.args[0] for w in warning_info.list] == [
        'Pydantic serializer warnings:\n  Expected `timedelta` but got `bytes` - '
        'serialized value may not be as expected'
    ]


def test_any_config_timedelta_float():
    s = SchemaSerializer(core_schema.any_schema(), config={'ser_json_timedelta': 'float'})
    h2 = timedelta(hours=2)
    assert s.to_python(h2) == h2
    assert s.to_python(h2, mode='json') == 7200.0
    assert s.to_json(h2) == b'7200.0'

    assert s.to_python({h2: 'foo'}) == {h2: 'foo'}
    assert s.to_python({h2: 'foo'}, mode='json') == {'7200': 'foo'}
    assert s.to_json({h2: 'foo'}) == b'{"7200":"foo"}'


def test_any_config_timedelta_float_faction():
    s = SchemaSerializer(core_schema.any_schema(), config={'ser_json_timedelta': 'float'})
    one_half_s = timedelta(seconds=1.5)
    assert s.to_python(one_half_s) == one_half_s
    assert s.to_python(one_half_s, mode='json') == 1.5
    assert s.to_json(one_half_s) == b'1.5'

    assert s.to_python({one_half_s: 'foo'}) == {one_half_s: 'foo'}
    assert s.to_python({one_half_s: 'foo'}, mode='json') == {'1.5': 'foo'}
    assert s.to_json({one_half_s: 'foo'}) == b'{"1.5":"foo"}'


def test_recursion(any_serializer):
    v = [1, 2]
    v.append(v)
    assert any_serializer.to_python(v) == v
    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        any_serializer.to_python(v, mode='json')
    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        any_serializer.to_json(v)


@pytest.mark.parametrize('seq_f', [as_list, as_tuple])
def test_include_list_tuple(any_serializer, seq_f):
    assert any_serializer.to_python(seq_f(0, 1, 2, 3)) == seq_f(0, 1, 2, 3)
    assert any_serializer.to_python(seq_f('a', 'b', 'c')) == seq_f('a', 'b', 'c')
    assert any_serializer.to_python(seq_f('a', 'b', 'c'), mode='json') == ['a', 'b', 'c']
    assert any_serializer.to_json(seq_f('a', 'b', 'c')) == b'["a","b","c"]'

    assert any_serializer.to_python(seq_f(0, 1, 2, 3), include={1, 2}) == seq_f(1, 2)
    assert any_serializer.to_python(seq_f(0, 1, 2, 3), include={1, 2}, mode='json') == [1, 2]
    assert any_serializer.to_python(seq_f('a', 'b', 'c', 'd'), include={1, 2}) == seq_f('b', 'c')
    assert any_serializer.to_python(seq_f('a', 'b', 'c', 'd'), include={1, 2}, mode='json') == ['b', 'c']
    assert any_serializer.to_json(seq_f('a', 'b', 'c', 'd'), include={1, 2}) == b'["b","c"]'


def as_generator(*items):
    return (v for v in items)


def test_include_generator(any_serializer):
    assert any_serializer.to_python(as_generator('a', 'b', 'c'), mode='json') == ['a', 'b', 'c']
    assert any_serializer.to_json(as_generator('a', 'b', 'c')) == b'["a","b","c"]'

    assert any_serializer.to_python(as_generator(0, 1, 2, 3), include={1, 2}, mode='json') == [1, 2]
    assert any_serializer.to_python(as_generator('a', 'b', 'c', 'd'), include={1, 2}, mode='json') == ['b', 'c']
    assert any_serializer.to_json(as_generator('a', 'b', 'c', 'd'), include={1, 2}) == b'["b","c"]'


def test_include_dict(any_serializer):
    assert any_serializer.to_python({1: 2, '3': 4}) == {1: 2, '3': 4}
    assert any_serializer.to_python(MyDataclass(a=1, b='foo', frog=2)) == {'a': 1, 'b': 'foo'}
    assert any_serializer.to_python({1: 2, '3': 4}, mode='json') == {'1': 2, '3': 4}
    assert any_serializer.to_json({1: 2, '3': 4}) == b'{"1":2,"3":4}'
    assert any_serializer.to_json(MyDataclass(a=1, b='foo', frog=2)) == b'{"a":1,"b":"foo"}'

    assert any_serializer.to_python({1: 2, '3': 4}, include={1}) == {1: 2}
    assert any_serializer.to_python({1: 2, '3': 4}, include={'3'}) == {'3': 4}
    assert any_serializer.to_python(MyDataclass(a=1, b='foo', frog=2), include={'a'}) == {'a': 1}
    assert any_serializer.to_python(MyDataclass(a=1, b='foo', frog=2), include={'a'}, mode='json') == {'a': 1}
    assert any_serializer.to_python(MyModel(a=1, b='foo'), include={'a'}) == {'a': 1}
    assert any_serializer.to_python(MyModel(a=1, b='foo'), include={'a'}, mode='json') == {'a': 1}
    assert any_serializer.to_python({1: 2, '3': 4}, include={1}, mode='json') == {'1': 2}
    assert any_serializer.to_python({1: 2, '3': 4}, include={'3'}, mode='json') == {'3': 4}
    assert any_serializer.to_json({1: 2, '3': 4}, include={1}) == b'{"1":2}'
    assert any_serializer.to_json({1: 2, '3': 4}, include={'3'}) == b'{"3":4}'
    assert any_serializer.to_json(MyDataclass(a=1, b='foo', frog=2), include={'a'}) == b'{"a":1}'


class FieldsSetModel:
    __pydantic_validator__ = 42
    __slots__ = '__dict__', '__fields_set__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_exclude_unset(any_serializer):
    # copied from test of the same name in test_model.py
    m = FieldsSetModel(foo=1, bar=2, spam=3, __fields_set__={'bar', 'spam'})
    assert any_serializer.to_python(m) == {'foo': 1, 'bar': 2, 'spam': 3}
    assert any_serializer.to_python(m, exclude_unset=True) == {'bar': 2, 'spam': 3}
    assert any_serializer.to_python(m, exclude=None, exclude_unset=True) == {'bar': 2, 'spam': 3}
    assert any_serializer.to_python(m, exclude={'bar'}, exclude_unset=True) == {'spam': 3}
    assert any_serializer.to_python(m, exclude={'bar': ...}, exclude_unset=True) == {'spam': 3}
    assert any_serializer.to_python(m, exclude={'bar': {}}, exclude_unset=True) == {'bar': 2, 'spam': 3}

    assert any_serializer.to_json(m, exclude=None, exclude_unset=True) == b'{"bar":2,"spam":3}'
    assert any_serializer.to_json(m, exclude={'bar'}, exclude_unset=True) == b'{"spam":3}'
    assert any_serializer.to_json(m, exclude={'bar': ...}, exclude_unset=True) == b'{"spam":3}'
    assert any_serializer.to_json(m, exclude={'bar': {}}, exclude_unset=True) == b'{"bar":2,"spam":3}'

    m2 = FieldsSetModel(foo=1, bar=2, spam=3, __fields_set__={'bar', 'spam', 'missing'})
    assert any_serializer.to_python(m2) == {'foo': 1, 'bar': 2, 'spam': 3}
    assert any_serializer.to_python(m2, exclude_unset=True) == {'bar': 2, 'spam': 3}


def test_unknown_type(any_serializer):
    class Foobar:
        def __repr__(self):
            return '<Foobar repr>'

    f = Foobar()
    assert any_serializer.to_python(f) == f

    with pytest.raises(PydanticSerializationError, match='Unable to serialize unknown type: <Foobar repr>'):
        any_serializer.to_python(f, mode='json')

    with pytest.raises(PydanticSerializationError, match='Unable to serialize unknown type: <Foobar repr>'):
        any_serializer.to_json(f)


class MyEnum(Enum):
    a = 1
    b = 'b'


def test_enum(any_serializer):

    assert any_serializer.to_python(MyEnum.a) == MyEnum.a
    assert any_serializer.to_python(MyEnum.b) == MyEnum.b
    assert any_serializer.to_python({MyEnum.a: 42}) == {MyEnum.a: 42}
    assert any_serializer.to_python({MyEnum.b: 42}) == {MyEnum.b: 42}

    assert any_serializer.to_python(MyEnum.a, mode='json') == 1
    assert any_serializer.to_python(MyEnum.b, mode='json') == 'b'
    assert any_serializer.to_python({MyEnum.a: 42}, mode='json') == {'1': 42}
    assert any_serializer.to_python({MyEnum.b: 42}, mode='json') == {'b': 42}

    assert any_serializer.to_json(MyEnum.a) == b'1'
    assert any_serializer.to_json(MyEnum.b) == b'"b"'
    assert any_serializer.to_json({MyEnum.a: 42}) == b'{"1":42}'
    assert any_serializer.to_json({MyEnum.b: 42}) == b'{"b":42}'


def test_base64():
    s = SchemaSerializer(core_schema.any_schema(), core_schema.CoreConfig(ser_json_bytes='base64'))
    assert s.to_python(b'foo') == b'foo'
    assert s.to_python(b'foo', mode='json') == 'Zm9v'
    assert s.to_json(b'foo') == b'"Zm9v"'
    assert s.to_python(bytearray(b'foo')) == b'foo'
    assert s.to_python(bytearray(b'foo'), mode='json') == 'Zm9v'
    assert s.to_json(bytearray(b'foo')) == b'"Zm9v"'


@pytest.mark.parametrize(
    'gen_input,kwargs,expected_json',
    [
        # (lambda: UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), '"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"'),
        (lambda: datetime(2032, 1, 1, 1, 1), {}, b'"2032-01-01T01:01:00"'),
        (lambda: datetime(2032, 1, 1, 1, 1, tzinfo=timezone.utc), {}, b'"2032-01-01T01:01:00Z"'),
        (lambda: datetime(2032, 1, 1, 1, 1, tzinfo=timezone(timedelta(hours=2))), {}, b'"2032-01-01T01:01:00+02:00"'),
        (lambda: datetime(2032, 1, 1), {}, b'"2032-01-01T00:00:00"'),
        (lambda: time(12, 34, 56), {}, b'"12:34:56"'),
        (lambda: timedelta(days=12, seconds=34, microseconds=56), {}, b'"P12DT34.000056S"'),
        (lambda: timedelta(days=12, seconds=34, microseconds=56), dict(timedelta_mode='float'), b'1036834.000056'),
        (lambda: timedelta(seconds=-1), {}, b'"-PT1S"'),
        (lambda: timedelta(seconds=-1), dict(timedelta_mode='float'), b'-1.0'),
        (lambda: {1, 2, 3}, {}, b'[1,2,3]'),
        (lambda: frozenset([1, 2, 3]), {}, b'[1,2,3]'),
        (lambda: (v for v in range(4)), {}, b'[0,1,2,3]'),
        (lambda: iter([0, 1, 2, 3]), {}, b'[0,1,2,3]'),
        (lambda: iter((0, 1, 2, 3)), {}, b'[0,1,2,3]'),
        (lambda: iter(range(4)), {}, b'[0,1,2,3]'),
        (lambda: b'this is bytes', {}, b'"this is bytes"'),
        (lambda: b'this is bytes', dict(bytes_mode='base64'), b'"dGhpcyBpcyBieXRlcw=="'),
        (lambda: bytearray(b'this is bytes'), {}, b'"this is bytes"'),
        (lambda: bytearray(b'this is bytes'), dict(bytes_mode='base64'), b'"dGhpcyBpcyBieXRlcw=="'),
        (lambda: Decimal('12.34'), {}, b'"12.34"'),
        (lambda: MyEnum.a, {}, b'1'),
        (lambda: MyEnum.b, {}, b'"b"'),
        (lambda: [MyDataclass(1, 'a', 2), MyModel(a=2, b='b')], {}, b'[{"a":1,"b":"a"},{"a":2,"b":"b"}]'),
        # # (lambda: re.compile('^regex$'), b'"^regex$"'),
    ],
)
def test_encoding(any_serializer, gen_input, kwargs, expected_json):
    assert to_json(gen_input(), **kwargs) == expected_json
    if not kwargs:
        assert any_serializer.to_python(gen_input(), mode='json') == json.loads(expected_json)
