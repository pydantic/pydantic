import re
import sys
from enum import Enum, IntFlag

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

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), missing=MyEnum._missing_))

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

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), missing=MyEnum._missing_))

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

    v = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), missing=MyEnum._missing_))
    with pytest.raises(TypeError, match=e):
        v.validate_python(3)


def test_enum_exactness():
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaValidator(
        core_schema.union_schema(
            [
                core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), missing=MyEnum._missing_),
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
