import re
from enum import Enum, IntEnum
from typing import Annotated, Any, NamedTuple

import pytest
from dirty_equals import IsStr
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    Strict,
    TypeAdapter,
    ValidationError,
)


def test_enum_successful():
    class ToolEnum(IntEnum):
        spanner = 1
        wrench = 2

    ta = TypeAdapter(ToolEnum)

    v = ta.validate_python(2)
    assert v == ToolEnum.wrench
    assert repr(v) == '<ToolEnum.wrench: 2>'


def test_enum_fails():
    class ToolEnum(IntEnum):
        spanner = 1
        wrench = 2

    ta = TypeAdapter(ToolEnum)

    with pytest.raises(ValueError) as exc_info:
        ta.validate_python(3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'expected': '1 or 2'},
            'input': 3,
            'loc': (),
            'msg': 'Input should be 1 or 2',
            'type': 'enum',
        }
    ]


def test_enum_fails_error_msg():
    class Number(IntEnum):
        one = 1
        two = 2
        three = 3

    ta = TypeAdapter(Number)

    with pytest.raises(ValueError) as exc_info:
        ta.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'enum',
            'loc': (),
            'msg': 'Input should be 1, 2 or 3',
            'input': 4,
            'ctx': {'expected': '1, 2 or 3'},
        }
    ]


def test_int_enum_successful_for_str_int():
    class ToolEnum(IntEnum):
        spanner = 1
        wrench = 2

    ta = TypeAdapter(ToolEnum)

    v = ta.validate_python('2')
    assert v == ToolEnum.wrench
    assert repr(v) == '<ToolEnum.wrench: 2>'


def test_plain_enum_validate():
    class MyEnum(Enum):
        a = 1

    class Model(BaseModel):
        x: MyEnum

    m = Model(x=MyEnum.a)
    assert m.x is MyEnum.a

    assert TypeAdapter(MyEnum).validate_python(1) is MyEnum.a
    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(MyEnum).validate_python(1, strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_plain_enum_validate.<locals>.MyEnum'},
            'input': 1,
            'loc': (),
            'msg': IsStr(regex='Input should be an instance of test_plain_enum_validate.<locals>.MyEnum'),
            'type': 'is_instance_of',
        }
    ]

    assert TypeAdapter(MyEnum).validate_json('1') is MyEnum.a
    TypeAdapter(MyEnum).validate_json('1', strict=True)
    with pytest.raises(ValidationError) as exc_info:
        TypeAdapter(MyEnum).validate_json('"1"', strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'ctx': {'expected': '1'}, 'input': '1', 'loc': (), 'msg': 'Input should be 1', 'type': 'enum'}
    ]


def test_plain_enum_validate_json():
    class MyEnum(Enum):
        a = 1

    class Model(BaseModel):
        x: MyEnum

    m = Model.model_validate_json('{"x":1}')
    assert m.x is MyEnum.a


def test_enum_type():
    class Model(BaseModel):
        my_enum: Enum

    class MyEnum(Enum):
        a = 1

    m = Model(my_enum=MyEnum.a)
    assert m.my_enum == MyEnum.a
    assert m.model_dump() == {'my_enum': MyEnum.a}
    assert m.model_dump_json() == '{"my_enum":1}'

    with pytest.raises(ValidationError) as exc_info:
        Model(my_enum=1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'Enum'},
            'input': 1,
            'loc': ('my_enum',),
            'msg': 'Input should be an instance of Enum',
            'type': 'is_instance_of',
        }
    ]


def test_enum_missing_default():
    class MyEnum(Enum):
        a = 1

    ta = TypeAdapter(MyEnum)
    missing_value = re.search(r'missing: (\w+)', repr(ta.validator)).group(1)
    assert missing_value == 'None'

    assert ta.validate_python(1) is MyEnum.a
    with pytest.raises(ValidationError):
        ta.validate_python(2)


def test_enum_missing_custom():
    class MyEnum(Enum):
        a = 1

        @classmethod
        def _missing_(cls, value):
            return MyEnum.a

    ta = TypeAdapter(MyEnum)
    missing_value = re.search(r'missing: (\w+)', repr(ta.validator)).group(1)
    assert missing_value == 'Some'

    assert ta.validate_python(1) is MyEnum.a
    assert ta.validate_python(2) is MyEnum.a


def test_int_enum_type():
    class Model(BaseModel):
        my_enum: IntEnum

    class MyEnum(Enum):
        a = 1

    class MyIntEnum(IntEnum):
        b = 2

    m = Model(my_enum=MyIntEnum.b)
    assert m.my_enum == MyIntEnum.b
    assert m.model_dump() == {'my_enum': MyIntEnum.b}
    assert m.model_dump_json() == '{"my_enum":2}'

    with pytest.raises(ValidationError) as exc_info:
        Model(my_enum=MyEnum.a)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'IntEnum'},
            'input': MyEnum.a,
            'loc': ('my_enum',),
            'msg': 'Input should be an instance of IntEnum',
            'type': 'is_instance_of',
        }
    ]


@pytest.mark.parametrize('enum_base,strict', [(Enum, False), (IntEnum, False), (IntEnum, True)])
def test_enum_from_json(enum_base, strict):
    class MyEnum(enum_base):
        a = 1
        b = 3

    class Model(BaseModel):
        my_enum: MyEnum

    m = Model.model_validate_json('{"my_enum":1}', strict=strict)
    assert m.my_enum is MyEnum.a

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate_json('{"my_enum":2}', strict=strict)

    if strict:
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'expected': '1 or 3'},
                'input': 2,
                'loc': ('my_enum',),
                'msg': 'Input should be 1 or 3',
                'type': 'enum',
            }
        ]
    else:
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'expected': '1 or 3'},
                'input': 2,
                'loc': ('my_enum',),
                'msg': 'Input should be 1 or 3',
                'type': 'enum',
            }
        ]


def test_strict_enum() -> None:
    class Demo(Enum):
        A = 0
        B = 1

    class User(BaseModel):
        model_config = ConfigDict(strict=True)

        demo_strict: Demo
        demo_not_strict: Demo = Field(strict=False)

    user = User(demo_strict=Demo.A, demo_not_strict=1)

    assert isinstance(user.demo_strict, Demo)
    assert isinstance(user.demo_not_strict, Demo)
    assert user.demo_strict.value == 0
    assert user.demo_not_strict.value == 1

    with pytest.raises(ValidationError, match='Input should be an instance of test_strict_enum.<locals>.Demo'):
        User(demo_strict=0, demo_not_strict=1)


def test_enum_with_no_cases() -> None:
    class MyEnum(Enum):
        pass

    class MyModel(BaseModel):
        e: MyEnum

    json_schema = MyModel.model_json_schema()
    assert json_schema['properties']['e']['enum'] == []


def test_enum_custom_schema() -> None:
    class MyEnum(str, Enum):
        foo = 'FOO'
        bar = 'BAR'
        baz = 'BAZ'

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
        ) -> CoreSchema:
            # check that we can still call handler
            handler(source_type)

            # return a custom unrelated schema so we can test that
            # it gets used
            schema = core_schema.union_schema(
                [
                    core_schema.str_schema(),
                    core_schema.is_instance_schema(cls),
                ]
            )
            return core_schema.no_info_after_validator_function(
                function=lambda x: MyEnum(x.upper()) if isinstance(x, str) else x,
                schema=schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda x: x.value, return_schema=core_schema.int_schema()
                ),
            )

    ta = TypeAdapter(MyEnum)

    assert ta.validate_python('foo') == MyEnum.foo


def test_diff_enums_diff_configs() -> None:
    class MyEnum(str, Enum):
        A = 'a'

    class MyModel(BaseModel, use_enum_values=True):
        my_enum: MyEnum

    class OtherModel(BaseModel):
        my_enum: MyEnum

    class Model(BaseModel):
        my_model: MyModel
        other_model: OtherModel

    obj = Model.model_validate({'my_model': {'my_enum': 'a'}, 'other_model': {'my_enum': 'a'}})
    assert not isinstance(obj.my_model.my_enum, MyEnum)
    assert isinstance(obj.other_model.my_enum, MyEnum)


def test_strict_enum_with_use_enum_values() -> None:
    class SomeEnum(int, Enum):
        SOME_KEY = 1

    class Foo(BaseModel):
        model_config = ConfigDict(strict=False, use_enum_values=True)
        foo: Annotated[SomeEnum, Strict(strict=True)]

    f = Foo(foo=SomeEnum.SOME_KEY)
    assert f.foo == 1

    # validation error raised bc foo field uses strict mode
    with pytest.raises(ValidationError):
        Foo(foo='1')


def test_enum_with_namedtuple_values() -> None:
    """https://github.com/pydantic/pydantic/issues/12503"""

    class NT(NamedTuple):
        f: str

    class SomeEnum(NT, Enum):
        FOO = 'foo'

    class Model1(BaseModel):
        value: SomeEnum

    assert Model1(value=SomeEnum.FOO).value is SomeEnum.FOO

    class Model2(BaseModel, use_enum_values=True):
        value: SomeEnum

    assert Model2(value=NT('foo')).value == NT('foo')

    with pytest.raises(ValidationError):
        Model2(value=NT('bar'))
