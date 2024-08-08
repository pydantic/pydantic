from enum import Enum

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_plain_enum():
    class MyEnum(Enum):
        a = 1
        b = 2

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())))

    # debug(v)
    assert v.to_python(MyEnum.a) is MyEnum.a
    assert v.to_python(MyEnum.a, mode='json') == 1
    assert v.to_json(MyEnum.a) == b'1'

    with pytest.warns(
        UserWarning, match='Expected `enum` but got `int` with value `1` - serialized value may not be as expected'
    ):
        assert v.to_python(1) == 1
    with pytest.warns(
        UserWarning, match='Expected `enum` but got `int` with value `1` - serialized value may not be as expected'
    ):
        assert v.to_json(1) == b'1'


def test_int_enum():
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='int'))

    # debug(v)
    assert v.to_python(MyEnum.a) is MyEnum.a
    assert v.to_python(MyEnum.a, mode='json') == 1
    assert v.to_json(MyEnum.a) == b'1'

    with pytest.warns(
        UserWarning, match='Expected `enum` but got `int` with value `1` - serialized value may not be as expected'
    ):
        assert v.to_python(1) == 1
    with pytest.warns(
        UserWarning, match='Expected `enum` but got `int` with value `1` - serialized value may not be as expected'
    ):
        assert v.to_json(1) == b'1'


def test_str_enum():
    class MyEnum(str, Enum):
        a = 'a'
        b = 'b'

    v = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='str'))

    # debug(v)
    assert v.to_python(MyEnum.a) is MyEnum.a
    assert v.to_python(MyEnum.a, mode='json') == 'a'
    assert v.to_json(MyEnum.a) == b'"a"'

    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'a'` - serialized value may not be as expected"
    ):
        assert v.to_python('a') == 'a'
    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'a'` - serialized value may not be as expected"
    ):
        assert v.to_json('a') == b'"a"'


def test_plain_dict_key():
    class MyEnum(Enum):
        a = 1
        b = 2

    v = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values())),
            core_schema.str_schema(),
        )
    )

    # debug(v)
    assert v.to_python({MyEnum.a: 'x'}) == {MyEnum.a: 'x'}
    assert v.to_python({MyEnum.a: 'x'}, mode='json') == {'1': 'x'}
    assert v.to_json({MyEnum.a: 'x'}) == b'{"1":"x"}'

    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'x'` - serialized value may not be as expected"
    ):
        assert v.to_python({'x': 'x'}) == {'x': 'x'}
    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'x'` - serialized value may not be as expected"
    ):
        assert v.to_json({'x': 'x'}) == b'{"x":"x"}'


def test_int_dict_key():
    class MyEnum(int, Enum):
        a = 1
        b = 2

    v = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.enum_schema(MyEnum, list(MyEnum.__members__.values()), sub_type='int'),
            core_schema.str_schema(),
        )
    )

    # debug(v)
    assert v.to_python({MyEnum.a: 'x'}) == {MyEnum.a: 'x'}
    assert v.to_python({MyEnum.a: 'x'}, mode='json') == {'1': 'x'}
    assert v.to_json({MyEnum.a: 'x'}) == b'{"1":"x"}'

    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'x'` - serialized value may not be as expected"
    ):
        assert v.to_python({'x': 'x'}) == {'x': 'x'}
    with pytest.warns(
        UserWarning, match="Expected `enum` but got `str` with value `'x'` - serialized value may not be as expected"
    ):
        assert v.to_json({'x': 'x'}) == b'{"x":"x"}'
