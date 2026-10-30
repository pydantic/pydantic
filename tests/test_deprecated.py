import re
from collections.abc import Iterable
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic_core import CoreSchema, core_schema

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    PydanticDeprecatedSince20,
    PydanticDeprecatedSince211,
    PydanticUserError,
    ValidationError,
    computed_field,
    conlist,
)
from pydantic.config import Extra
from pydantic.deprecated.decorator import validate_arguments
from pydantic.deprecated.json import custom_pydantic_encoder, pydantic_encoder, timedelta_isoformat
from pydantic.deprecated.parse import load_file, load_str_bytes
from pydantic.deprecated.tools import parse_obj_as, schema_json_of, schema_of
from pydantic.json_schema import JsonSchemaValue
from pydantic.type_adapter import TypeAdapter

# `pytest.warns/raises()` is thread unsafe. As these tests are meant to be
# removed in V3, we just mark all tests as thread unsafe
pytestmark = pytest.mark.thread_unsafe


def test_fields():
    class Model(BaseModel):
        x: int
        y: int = 2

        @computed_field
        @property
        def area(self) -> int:
            return self.x * self.y

    m = Model(x=1)
    assert len(Model.model_fields) == 2

    with pytest.warns(PydanticDeprecatedSince211, match="Accessing the 'model_fields' attribute"):
        assert len(m.model_fields) == 2

    with pytest.warns(PydanticDeprecatedSince211, match="Accessing the 'model_computed_fields' attribute"):
        assert len(m.model_computed_fields) == 1


@pytest.mark.parametrize('attribute,value', [('allow', 'allow'), ('ignore', 'ignore'), ('forbid', 'forbid')])
def test_extra_used_as_enum(
    attribute: str,
    value: str,
) -> None:
    with pytest.warns(
        PydanticDeprecatedSince20,
        match=re.escape("`pydantic.config.Extra` is deprecated, use literal values instead (e.g. `extra='allow'`)"),
    ):
        assert getattr(Extra, attribute) == value


def test_field_min_items_deprecation():
    m = '`min_items` is deprecated and will be removed. use `min_length` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: list[int] = Field(None, min_items=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('x',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_field_min_items_with_min_length():
    m = '`min_items` is deprecated and will be removed. use `min_length` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: list[int] = Field(None, min_items=1, min_length=2)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('x',),
            'msg': 'List should have at least 2 items after validation, not 1',
            'input': [1],
            'ctx': {'field_type': 'List', 'min_length': 2, 'actual_length': 1},
        }
    ]


def test_field_max_items():
    m = '`max_items` is deprecated and will be removed. use `max_length` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: list[int] = Field(None, max_items=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('x',),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]


def test_field_max_items_with_max_length():
    m = '`max_items` is deprecated and will be removed. use `max_length` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: list[int] = Field(None, max_items=1, max_length=2)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1, 2, 3])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('x',),
            'msg': 'List should have at most 2 items after validation, not 3',
            'input': [1, 2, 3],
            'ctx': {'field_type': 'List', 'max_length': 2, 'actual_length': 3},
        }
    ]


def test_field_const():
    with pytest.raises(PydanticUserError, match='`const` is removed. use `Literal` instead'):

        class Model(BaseModel):
            x: str = Field('test', const=True)


def test_field_include_deprecation():
    with pytest.warns(PydanticDeprecatedSince20) as all_warnings:

        class Model(BaseModel):
            x: int = Field(include=True)

    assert len(all_warnings) == 2
    expected_warnings = [
        "Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'include')",
        '`include` is deprecated and does nothing. It will be removed, use `exclude` instead',
    ]
    assert [w.message.message for w in all_warnings] == expected_warnings


def test_unique_items_items():
    with pytest.raises(PydanticUserError, match='`unique_items` is removed. use `Set` instead'):

        class Model(BaseModel):
            x: list[int] = Field(None, unique_items=True)


def test_unique_items_conlist():
    with pytest.raises(PydanticUserError, match='`unique_items` is removed. use `Set` instead'):

        class Model(BaseModel):
            x: conlist(int, unique_items=True)


def test_allow_mutation():
    m = '`allow_mutation` is deprecated and will be removed. use `frozen` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            model_config = ConfigDict(validate_assignment=True)
            x: int = Field(allow_mutation=False)
            y: int = Field(allow_mutation=True)

    m = Model(x=1, y=2)

    assert m.x == 1
    with pytest.raises(ValidationError) as exc_info:
        m.x = 2
    assert exc_info.value.errors(include_url=False) == [
        {'input': 2, 'loc': ('x',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]

    m.y = 3
    assert m.y == 3


def test_field_regex():
    with pytest.raises(PydanticUserError, match='`regex` is removed. use `pattern` instead'):

        class Model(BaseModel):
            x: str = Field('test', regex=r'^test$')


def test_modify_schema_error():
    with pytest.raises(
        PydanticUserError,
        match='The `__modify_schema__` method is not supported in Pydantic v2. '
        'Use `__get_pydantic_json_schema__` instead in class `Model`.',
    ):

        class Model(BaseModel):
            @classmethod
            def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
                pass


def test_modify_schema_on_nested_class_error() -> None:
    class SomeLongName:
        @classmethod
        def __modify_schema__(cls, field_schema):
            pass

    with pytest.raises(
        PydanticUserError,
        match='The `__modify_schema__` method is not supported in Pydantic v2. '
        'Use `__get_pydantic_json_schema__` instead in class `SomeLongName`.',
    ):

        class B(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)

            a: SomeLongName


def test_v1_v2_custom_type_compatibility() -> None:
    """Create a custom type that works with V1 and V2"""

    class MyType:
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            return core_schema.int_schema()

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            return {'anyOf': [{'type': 'string'}, {'type': 'number'}]}

        @classmethod
        def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
            raise NotImplementedError  # not actually called, we just want to make sure the method can exist

        @classmethod
        def __get_validators__(cls) -> Iterable[Any]:
            raise NotImplementedError  # not actually called, we just want to make sure the method can exist
            yield

    ta = TypeAdapter(MyType)
    assert ta.validate_python('123') == 123
    assert ta.json_schema() == {'anyOf': [{'type': 'string'}, {'type': 'number'}]}


def test_v1_get_validators():
    class CustomDate(date):
        @classmethod
        def __get_validators__(cls):
            yield cls.validate1
            yield cls.validate2

        @classmethod
        def validate1(cls, v, i):
            print(v)

            if v.year < 2000:
                raise ValueError('Invalid year')
            return v

        @classmethod
        def validate2(cls, v, i):
            return date.today().replace(month=1, day=1)

    with pytest.warns(
        PydanticDeprecatedSince20,
        match='^`__get_validators__` is deprecated and will be removed, use `__get_pydantic_core_schema__` instead.',
    ):

        class Model(BaseModel):
            x: CustomDate

    with pytest.raises(ValidationError, match='Value error, Invalid year'):
        Model(x=date(1999, 1, 1))

    m = Model(x=date.today())
    assert m.x.day == 1


def test_v1_get_validators_invalid_validator():
    class InvalidValidator:
        @classmethod
        def __get_validators__(cls):
            yield cls.has_wrong_arguments

        @classmethod
        def has_wrong_arguments(cls):
            pass

    with pytest.warns(
        PydanticDeprecatedSince20,
        match='^`__get_validators__` is deprecated and will be removed, use `__get_pydantic_core_schema__` instead.',
    ):

        class InvalidValidatorModel(BaseModel):
            x: InvalidValidator

    with pytest.raises(TypeError, match='takes 1 positional argument but 3 were given'):
        InvalidValidatorModel(x=1)


def test_field_extra_arguments():
    m = re.escape(
        'Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. '
        "(Extra keys: 'test', 'foo')"
    )
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: str = Field('test', test='test', foo='bar')

    assert Model.model_json_schema(by_alias=True)['properties'] == {
        'x': {'default': 'test', 'foo': 'bar', 'test': 'test', 'title': 'X', 'type': 'string'}
    }


def test_field_extra_does_not_rewrite_json_schema_extra():
    m = 'Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead'
    with pytest.warns(PydanticDeprecatedSince20, match=m):

        class Model(BaseModel):
            x: str = Field('test', test='test', json_schema_extra={'test': 'json_schema_extra value'})

    assert Model.model_json_schema(by_alias=True)['properties'] == {
        'x': {'default': 'test', 'test': 'json_schema_extra value', 'title': 'X', 'type': 'string'}
    }


def test_deprecated_module(tmp_path: Path) -> None:
    class Model(BaseModel):
        x: int

    with pytest.warns(PydanticDeprecatedSince20) as all_warnings:
        assert hasattr(parse_obj_as, '__deprecated__')
        parse_obj_as(Model, {'x': 1})
        assert hasattr(schema_json_of, '__deprecated__')
        schema_json_of(Model)
        assert hasattr(schema_of, '__deprecated__')
        schema_of(Model)
        assert hasattr(load_str_bytes, '__deprecated__')
        load_str_bytes('{"x": 1}')
        assert hasattr(load_file, '__deprecated__')
        file = tmp_path / 'main.py'
        file.write_text('{"x": 1}')
        load_file(file)
        assert hasattr(pydantic_encoder, '__deprecated__')
        pydantic_encoder(Model(x=1))
        assert hasattr(custom_pydantic_encoder, '__deprecated__')
        custom_pydantic_encoder({int: lambda x: str(x)}, Model(x=1))
        assert hasattr(timedelta_isoformat, '__deprecated__')
        timedelta_isoformat(timedelta(seconds=1))

        def test(a: int, b: int):
            pass

        validate_arguments()(test)
    assert len(all_warnings) == 12
    expected_warnings = [
        '`parse_obj_as` is deprecated. Use `pydantic.TypeAdapter.validate_python` instead',
        '`schema_json_of` is deprecated. Use `pydantic.TypeAdapter.json_schema` instead',
        '`schema_of` is deprecated. Use `pydantic.TypeAdapter.json_schema` instead',
        '`schema_of` is deprecated. Use `pydantic.TypeAdapter.json_schema` instead',
        '`load_str_bytes` is deprecated',
        '`load_file` is deprecated',
        '`load_str_bytes` is deprecated',
        '`pydantic_encoder` is deprecated, use `pydantic_core.to_jsonable_python` instead',
        '`custom_pydantic_encoder` is deprecated, use `BaseModel.model_dump` instead',
        '`pydantic_encoder` is deprecated, use `pydantic_core.to_jsonable_python` instead',
        '`timedelta_isoformat` is deprecated',
        'The `validate_arguments` method is deprecated; use `validate_call` instead',
    ]
    assert [w.message.message for w in all_warnings] == expected_warnings


def test_deprecated_color():
    from pydantic.color import Color

    with pytest.warns(
        PydanticDeprecatedSince20, match='The `Color` class is deprecated, use `pydantic_extra_types` instead.'
    ):
        Color('red')


def test_deprecated_payment():
    from pydantic import PaymentCardNumber

    with pytest.warns(
        PydanticDeprecatedSince20,
        match='The `PaymentCardNumber` class is deprecated, use `pydantic_extra_types` instead.',
    ):
        PaymentCardNumber('4242424242424242')
