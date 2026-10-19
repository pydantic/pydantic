import json
import re
import sys
from decimal import Decimal
from enum import Enum, IntEnum, IntFlag

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema


def test_plain_enum():
    class MyEnum(Enum):
        a = 1
        b = 2

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    # debug(v)
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(MyEnum.b) is MyEnum.b
    assert v.validate_python(1) is MyEnum.a
    assert v.validate_python(2) is MyEnum.b

    assert v.validate_json('1') is MyEnum.a
    # assert v.validate_json('"1"') is MyEnum.a

    with pytest.raises(ValidationError, match=r'Input should be 1 or 2 \[type=enum, input_value=3, input_type=int\]'):
        v.validate_python(3)

    with pytest.raises(ValidationError, match=r"Input should be 1 or 2 \[type=enum, input_value='1', input_type=str\]"):
        v.validate_python('1')

    assert v.validate_python(MyEnum.a, strict=True) is MyEnum.a

    e = (
        'Input should be an instance of test_plain_enum.<locals>.MyEnum '
        '[type=is_instance_of, input_value=1, input_type=int]'
    )
    with pytest.raises(ValidationError, match=re.escape(e)):
        v.validate_python(1, strict=True)

    assert v.validate_json('1', strict=True) is MyEnum.a
    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_json('"1"', strict=True)

    v_strict = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), strict=True))
    assert v_strict.validate_python(MyEnum.a) is MyEnum.a

    with pytest.raises(ValidationError, match=re.escape(e)):
        v_strict.validate_python(1, strict=True)

    v_strict_f = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), strict=True))
    assert v_strict_f.validate_python(MyEnum.a) is MyEnum.a

    with pytest.raises(ValidationError, match=re.escape(e)):
        v_strict_f.validate_python(1, strict=True)


@pytest.mark.parametrize('schema_strict,strict', [(False, None), (False, True), (True, None), (True, False)])
def test_plain_enum_json_key(schema_strict, strict):
    class Status(Enum):
        OK = 200
        NOT_FOUND = 404

    v = SchemaValidator(
        core_schema.dict_schema(
            core_schema.enum_schema(Status, list(Status), strict=schema_strict), core_schema.int_schema()
        )
    )
    result = v.validate_json('{"200":3,"404":1}', strict=strict)
    assert result == {Status.OK: 3, Status.NOT_FOUND: 1}
    assert list(result) == [Status.OK, Status.NOT_FOUND]


@pytest.mark.parametrize('value', [-(2**63), 2**63 - 1, -(2**63) - 1, 2**63])
@pytest.mark.parametrize('mixed', [False, True])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_integer_boundaries(value, mixed, strict):
    members = {'TARGET': value}
    if mixed:
        members['SMALL'] = 200
    Status = Enum('Status', members)
    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    data = {str(value): 3}
    expected = {Status.TARGET: 3}
    if mixed:
        data['200'] = 1
        expected[Status.SMALL] = 1
    assert v.validate_json(json.dumps(data), strict=strict) == expected


@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_large_only(strict):
    class Status(Enum):
        BELOW = -(2**63) - 1
        ABOVE = 2**63

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    data = {str(Status.BELOW.value): 3, str(Status.ABOVE.value): 1}
    assert v.validate_json(json.dumps(data), strict=strict) == {Status.BELOW: 3, Status.ABOVE: 1}


@pytest.mark.parametrize('value', [200, 2**63])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_duplicate_integer_precedence(value, strict):
    class Status(Enum):
        FIRST = value
        SECOND = value + 1

    # Give distinct members equal values in the schema to exercise lookup precedence.
    Status.SECOND._value_ = value
    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    assert v.validate_python({value: 3}) == {Status.SECOND: 3}
    assert v.validate_json(json.dumps({str(value): 3}), strict=strict) == {Status.SECOND: 3}


@pytest.mark.parametrize('value_type', ['float', 'int-subclass'])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_requires_exact_integer_value(value_type, strict):
    class MyInt(int):
        pass

    value = 200.0 if value_type == 'float' else MyInt(200)
    Status = Enum('Status', {'OK': value})
    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_json('{"200":3}', strict=strict)


@pytest.mark.parametrize('key', [str(-(2**63) - 2), str(2**63 + 1)])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_unmatched_large_integer_preserves_error(key, strict):
    class Status(Enum):
        OK = 200
        LARGE = 2**63

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json(json.dumps({key: 3}), strict=strict)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'enum',
            'loc': (key, '[key]'),
            'msg': 'Input should be 200 or 9223372036854775808',
            'input': key,
            'ctx': {'expected': '200 or 9223372036854775808'},
        }
    ]


@pytest.mark.parametrize('value', [200, 2**63])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_does_not_coerce_other_strings(value, strict):
    class Status(Enum):
        OK = value

    schema = core_schema.enum_schema(Status, list(Status))
    v = SchemaValidator(schema)
    key = str(value)
    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_json(json.dumps(key), strict=strict)
    with pytest.raises(ValidationError, match='type=is_instance_of' if strict else 'type=enum'):
        v.validate_python(key, strict=strict)
    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_strings(key, strict=strict)

    d = SchemaValidator(core_schema.dict_schema(schema, core_schema.int_schema()))
    with pytest.raises(ValidationError, match='type=is_instance_of' if strict else 'type=enum'):
        d.validate_python({key: 3}, strict=strict)
    with pytest.raises(ValidationError, match='type=enum'):
        d.validate_strings({key: '3'}, strict=strict)


@pytest.mark.parametrize('value', [200, 2**63])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_string_member_precedence(value, strict):
    calls = []

    class Status(Enum):
        NUMBER = value
        TEXT = str(value)

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            return cls.NUMBER

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    assert v.validate_json(json.dumps({str(value): 3}), strict=strict) == {Status.TEXT: 3}
    assert calls == []


@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_missing_precedence(strict):
    calls = []

    class Status(Enum):
        OK = 200
        NOT_FOUND = 404

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            return cls.NOT_FOUND

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    assert v.validate_json('{"200":3}', strict=strict) == {Status.NOT_FOUND: 3}
    assert calls == ['200']


def test_plain_enum_json_key_constructor_alias_precedence():
    class Status(Enum):
        OK = 200
        NOT_FOUND = 404

    # Match the extra value mappings exercised by test_support_custom_new_method.
    Status._value2member_map_['200'] = Status.NOT_FOUND
    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    assert v.validate_json('{"200":3}') == {Status.NOT_FOUND: 3}


@pytest.mark.parametrize('value', [200, 2**63])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_recovery_after_missing_none(value, strict):
    calls = []

    class Status(Enum):
        OK = value

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            return None

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    assert v.validate_json(json.dumps({str(value): 3}), strict=strict) == {Status.OK: 3}
    assert calls == [str(value)]


@pytest.mark.parametrize('value', [200, 2**63])
@pytest.mark.parametrize('strict', [False, True])
def test_plain_enum_json_key_recovery_after_missing_value_error(value, strict):
    calls = []

    class Status(Enum):
        OK = value

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            raise ValueError('not a member')

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    # Constructor ValueError is recoverable when the numeric key matches a member.
    assert v.validate_json(json.dumps({str(value): 3}), strict=strict) == {Status.OK: 3}
    assert calls == [str(value)]


def test_plain_enum_json_key_missing_value_error_preserves_error():
    calls = []

    class Status(Enum):
        OK = 200
        NOT_FOUND = 404

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            raise ValueError('not a member')

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"999":3}')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'enum',
            'loc': ('999', '[key]'),
            'msg': 'Input should be 200 or 404',
            'input': '999',
            'ctx': {'expected': '200 or 404'},
        }
    ]
    assert calls == ['999']


@pytest.mark.parametrize('key', ['999', 'not-an-int', str(1 << 63)])
def test_plain_enum_json_key_preserves_error(key):
    calls = []

    class Status(Enum):
        OK = 200
        NOT_FOUND = 404

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            return None

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"' + key + '":3}')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'enum',
            'loc': (key, '[key]'),
            'msg': 'Input should be 200 or 404',
            'input': key,
            'ctx': {'expected': '200 or 404'},
        }
    ]
    assert calls == [key]


@pytest.mark.parametrize('error_type', [TypeError, RuntimeError])
def test_plain_enum_json_key_missing_exception(error_type):
    calls = []

    class Status(Enum):
        OK = 200

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            raise error_type('hook rejection')

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(error_type, match='hook rejection'):
        v.validate_json('{"200":3}')
    assert calls == ['200']


def test_plain_enum_json_key_missing_wrong():
    calls = []

    class Status(Enum):
        OK = 200

        @classmethod
        def _missing_(cls, value):
            calls.append(value)
            return 'not a member'

    v = SchemaValidator(
        core_schema.dict_schema(core_schema.enum_schema(Status, list(Status)), core_schema.int_schema())
    )
    with pytest.raises(TypeError, match='instead of None or a valid member'):
        v.validate_json('{"200":3}')
    assert calls == ['200']


@pytest.mark.parametrize('wrapper', ['before', 'wrap'])
def test_plain_enum_json_key_requires_native_input(wrapper):
    class Status(Enum):
        OK = 200

    schema = core_schema.enum_schema(Status, list(Status))
    if wrapper == 'before':
        schema = core_schema.no_info_before_validator_function(lambda value: value, schema)
    else:
        schema = core_schema.no_info_wrap_validator_function(lambda value, handler: handler(value), schema)
    v = SchemaValidator(core_schema.dict_schema(schema, core_schema.int_schema()))
    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_json('{"200":3}')


def test_int_enum():
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='int'))

    # debug(v)
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1) is MyEnum.a
    assert v.validate_python(1.0) is MyEnum.a
    assert v.validate_python('1') is MyEnum.a

    assert v.validate_json('1') is MyEnum.a
    assert v.validate_json('"1"') is MyEnum.a

    with pytest.raises(ValidationError, match=r'Input should be 1 or 2 \[type=enum, input_value=3, input_type=int\]'):
        v.validate_python(3)

    assert v.validate_python(MyEnum.a, strict=True) is MyEnum.a

    e = (
        'Input should be an instance of test_int_enum.<locals>.MyEnum '
        '[type=is_instance_of, input_value=1, input_type=int]'
    )
    with pytest.raises(ValidationError, match=re.escape(e)):
        v.validate_python(1, strict=True)

    assert v.validate_json('1', strict=True) is MyEnum.a

    with pytest.raises(ValidationError, match=r"Input should be 1 or 2 \[type=enum, input_value='1', input_type=str\]"):
        v.validate_json('"1"', strict=True)


def test_str_enum():
    class MyEnum(str, Enum):
        a = 'x'
        b = 'y'

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='str'))

    # debug(v)
    assert v.validate_python('x') is MyEnum.a
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(b'x') is MyEnum.a

    assert v.validate_json('"x"') is MyEnum.a

    with pytest.raises(
        ValidationError, match=r"Input should be 'x' or 'y' \[type=enum, input_value='a', input_type=str\]"
    ):
        v.validate_python('a')

    assert v.validate_python(MyEnum.a, strict=True) is MyEnum.a

    e = (
        'Input should be an instance of test_str_enum.<locals>.MyEnum '
        "[type=is_instance_of, input_value='x', input_type=str]"
    )
    with pytest.raises(ValidationError, match=re.escape(e)):
        v.validate_python('x', strict=True)
    assert v.validate_json('"x"', strict=True) is MyEnum.a


def test_float_enum():
    class MyEnum(float, Enum):
        a = 1.5
        b = 2.5
        c = 3.0

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='float'))

    # debug(v)
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1.5) is MyEnum.a
    assert v.validate_python('1.5') is MyEnum.a
    assert v.validate_python(3) is MyEnum.c

    assert v.validate_json('1.5') is MyEnum.a
    assert v.validate_json('"1.5"') is MyEnum.a

    e = r'Input should be 1.5, 2.5 or 3.0 \[type=enum, input_value=4.0, input_type=float\]'
    with pytest.raises(ValidationError, match=e):
        v.validate_python(4.0)

    assert v.validate_python(MyEnum.a, strict=True) is MyEnum.a

    e = (
        'Input should be an instance of test_float_enum.<locals>.MyEnum '
        '[type=is_instance_of, input_value=1.5, input_type=float]'
    )
    with pytest.raises(ValidationError, match=re.escape(e)):
        v.validate_python(1.5, strict=True)

    assert v.validate_json('1.5', strict=True) is MyEnum.a

    with pytest.raises(ValidationError, match='type=enum'):
        v.validate_json('"3.0"', strict=True)


def test_enum_missing():
    class MyEnum(Enum):
        a = 1
        b = 2

        @classmethod
        def _missing_(cls, v):
            return cls.b

    assert MyEnum(1) is MyEnum.a
    assert MyEnum(2) is MyEnum.b
    assert MyEnum(3) is MyEnum.b

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    # debug(v)
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1) is MyEnum.a
    assert v.validate_python(2) is MyEnum.b
    assert v.validate_python(3) is MyEnum.b

    assert v.validate_json('1') is MyEnum.a
    assert v.validate_json('3') is MyEnum.b


def test_enum_missing_none():
    class MyEnum(Enum):
        a = 1
        b = 2

        @classmethod
        def _missing_(cls, v):
            return None

    assert MyEnum(1) is MyEnum.a
    assert MyEnum(2) is MyEnum.b
    with pytest.raises(ValueError, match='3 is not a valid'):
        MyEnum(3)

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    # debug(v)
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1) is MyEnum.a
    with pytest.raises(ValidationError, match=r'Input should be 1 or 2 \[type=enum, input_value=3, input_type=int\]'):
        v.validate_python(3)

    assert v.validate_json('1') is MyEnum.a
    with pytest.raises(ValidationError, match=r'Input should be 1 or 2 \[type=enum, input_value=3, input_type=int\]'):
        v.validate_json('3')


def test_enum_missing_wrong():
    class MyEnum(Enum):
        a = 1
        b = 2

        @classmethod
        def _missing_(cls, v):
            return 'foobar'

    assert MyEnum(1) is MyEnum.a
    assert MyEnum(2) is MyEnum.b
    # different error from pypy
    if sys.implementation.name == 'pypy':
        e = "returned 'foobar' instead of None or a valid member"
    else:
        e = "error in MyEnum._missing_: returned 'foobar' instead of None or a valid member"
    with pytest.raises(TypeError, match=e):
        MyEnum(3)

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))
    with pytest.raises(TypeError, match=e):
        v.validate_python(3)
    with pytest.raises(TypeError, match=e):
        v.validate_json('3')


def test_enum_exactness():
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaValidator(
        core_schema.union_schema(
            [
                core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
                core_schema.int_schema(),
            ],
        )
    )
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1) == 1
    assert v.validate_python(1) is not MyEnum.a


def test_plain_enum_lists():
    class MyEnum(Enum):
        a = [1]
        b = [2]

    assert MyEnum([1]) is MyEnum.a
    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))
    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python([1]) is MyEnum.a
    assert v.validate_python([2]) is MyEnum.b


def test_plain_enum_empty():
    class MyEnum(Enum):
        pass

    with pytest.raises(SchemaError, match='`members` should have length > 0'):
        SchemaValidator(core_schema.enum_schema(MyEnum, []))


def test_enum_with_str_subclass() -> None:
    class MyEnum(Enum):
        a = 'a'
        b = 'b'

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python('a') is MyEnum.a

    class MyStr(str):
        pass

    assert v.validate_python(MyStr('a')) is MyEnum.a
    with pytest.raises(ValidationError):
        v.validate_python(MyStr('a'), strict=True)


def test_enum_with_int_subclass() -> None:
    class MyEnum(Enum):
        a = 1
        b = 2

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    assert v.validate_python(MyEnum.a) is MyEnum.a
    assert v.validate_python(1) is MyEnum.a

    class MyInt(int):
        pass

    assert v.validate_python(MyInt(1)) is MyEnum.a
    with pytest.raises(ValidationError):
        v.validate_python(MyInt(1), strict=True)


def test_validate_float_for_int_enum() -> None:
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    assert v.validate_python(1.0) is MyEnum.a


def test_missing_error_converted_to_val_error() -> None:
    class MyFlags(IntFlag):
        OFF = 0
        ON = 1

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyFlags, list(MyFlags.__members__.values())), default=MyFlags.OFF
        )
    )

    assert v.validate_python(MyFlags.OFF) is MyFlags.OFF
    assert v.validate_python(0) is MyFlags.OFF

    with pytest.raises(ValidationError):
        v.validate_python(None)


def test_big_int():
    class ColorEnum(IntEnum):
        GREEN = 1 << 63
        BLUE = 1 << 64

    v = SchemaValidator(
        core_schema.with_default_schema(schema=core_schema.enum_schema(ColorEnum, list(ColorEnum.__members__.values())))
    )

    assert v.validate_python(ColorEnum.GREEN) is ColorEnum.GREEN
    assert v.validate_python(1 << 63) is ColorEnum.GREEN


@pytest.mark.parametrize(
    'value',
    [-1, 0, 1],
)
def test_enum_int_validation_should_succeed_for_decimal(value: int):
    class MyEnum(Enum):
        VALUE = value

    class MyIntEnum(IntEnum):
        VALUE = value

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            default=MyEnum.VALUE,
        )
    )

    v_int = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyIntEnum, list(MyIntEnum.__members__.values())),
            default=MyIntEnum.VALUE,
        )
    )

    assert v.validate_python(Decimal(value)) is MyEnum.VALUE
    assert v.validate_python(Decimal(float(value))) is MyEnum.VALUE
    assert v_int.validate_python(Decimal(value)) is MyIntEnum.VALUE
    assert v_int.validate_python(Decimal(float(value))) is MyIntEnum.VALUE


@pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason='Python 3.13+ enum initialization is different, see https://github.com/python/cpython/blob/ec610069637d56101896803a70d418a89afe0b4b/Lib/enum.py#L1159-L1163',
)
def test_enum_int_validation_should_succeed_for_custom_type():
    class AnyWrapper:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other: object) -> bool:
            return self.value == other

    class MyEnum(Enum):
        VALUE = 999
        SECOND_VALUE = 1000000
        THIRD_VALUE = 'Py03'

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            default=MyEnum.VALUE,
        )
    )

    assert v.validate_python(AnyWrapper(999)) is MyEnum.VALUE
    assert v.validate_python(AnyWrapper(1000000)) is MyEnum.SECOND_VALUE
    assert v.validate_python(AnyWrapper('Py03')) is MyEnum.THIRD_VALUE


def test_enum_str_validation_should_fail_for_decimal_when_expecting_str_value():
    class MyEnum(Enum):
        VALUE = '1'

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            default=MyEnum.VALUE,
        )
    )

    with pytest.raises(ValidationError):
        v.validate_python(Decimal(1))


def test_enum_int_validation_should_fail_for_incorrect_decimal_value():
    class MyEnum(Enum):
        VALUE = 1

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            default=MyEnum.VALUE,
        )
    )

    with pytest.raises(ValidationError):
        v.validate_python(Decimal(2))

    with pytest.raises(ValidationError):
        v.validate_python((1, 2))

    with pytest.raises(ValidationError):
        v.validate_python(Decimal(1.1))


def test_enum_int_validation_should_fail_for_plain_type_without_eq_checking():
    class MyEnum(Enum):
        VALUE = 1

    class MyClass:
        def __init__(self, value):
            self.value = value

    v = SchemaValidator(
        core_schema.with_default_schema(
            schema=core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            default=MyEnum.VALUE,
        )
    )

    with pytest.raises(ValidationError):
        v.validate_python(MyClass(1))


def test_support_custom_new_method() -> None:
    """Demonstrates support for custom new methods, as well as conceptually, multi-value enums without dependency on a 3rd party lib for testing."""

    class Animal(Enum):
        CAT = 'cat', 'meow'
        DOG = 'dog', 'woof'

        def __new__(cls, species: str, sound: str):
            obj = object.__new__(cls)

            obj._value_ = species
            obj._all_values = (species, sound)

            obj.species = species
            obj.sound = sound

            cls._value2member_map_[sound] = obj

            return obj

    v = SchemaValidator(core_schema.enum_schema(Animal, list(Animal.__members__.values())))
    assert v.validate_python('cat') is Animal.CAT
    assert v.validate_python('meow') is Animal.CAT
    assert v.validate_python('dog') is Animal.DOG
    assert v.validate_python('woof') is Animal.DOG


def test_strict_enum_wrap_json() -> None:
    """https://github.com/pydantic/pydantic/issues/11070"""

    class Animal(str, Enum):
        CAT = 'cat'
        DOG = 'dog'

    schema = core_schema.no_info_wrap_validator_function(
        lambda v, handler: handler(v),
        core_schema.enum_schema(Animal, list(Animal.__members__.values()), sub_type='str', strict=True),
    )
    v = SchemaValidator(schema)

    assert v.validate_python(Animal.CAT) == Animal.CAT
    assert v.validate_json('"dog"') == Animal.DOG
