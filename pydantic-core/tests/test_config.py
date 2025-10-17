import math
import re

import pytest
from dirty_equals import FunctionCheck, HasAttributes, IsInstance

from pydantic_core import CoreConfig, SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from .conftest import Err, plain_repr


def test_on_field():
    v = SchemaValidator(cs.str_schema(min_length=2, max_length=5))
    r = plain_repr(v)
    assert 'min_length:Some(2)' in r
    assert 'max_length:Some(5)' in r
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


def test_on_config():
    v = SchemaValidator(cs.str_schema(), config=CoreConfig(str_max_length=5))
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


def test_field_priority_arg():
    v = SchemaValidator(cs.str_schema(max_length=5), config=CoreConfig(str_max_length=10))
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


class MyModel:
    # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def test_on_model_class():
    v = SchemaValidator(
        cs.model_schema(
            cls=MyModel,
            config=CoreConfig(str_max_length=5),
            schema=cs.model_fields_schema(fields={'f': cs.model_field(schema=cs.str_schema())}),
        )
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_field_priority_model():
    v = SchemaValidator(
        cs.model_schema(
            cls=MyModel,
            config=CoreConfig(str_max_length=10),
            schema=cs.model_fields_schema(fields={'f': cs.model_field(schema=cs.str_schema(max_length=5))}),
        )
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


@pytest.mark.parametrize(
    'config,float_field_schema,input_value,expected',
    [
        (
            CoreConfig(),
            cs.float_schema(),
            {'x': 'nan'},
            IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan)),
        ),
        (
            CoreConfig(allow_inf_nan=True),
            cs.float_schema(),
            {'x': 'nan'},
            IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan)),
        ),
        (
            CoreConfig(allow_inf_nan=False),
            cs.float_schema(),
            {'x': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
        # field `allow_inf_nan` (if set) should have priority over global config
        (
            CoreConfig(allow_inf_nan=True),
            cs.float_schema(allow_inf_nan=False),
            {'x': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
        (
            CoreConfig(allow_inf_nan=False),
            cs.float_schema(allow_inf_nan=True),
            {'x': 'nan'},
            IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan)),
        ),
    ],
    ids=repr,
)
def test_allow_inf_nan(config: CoreConfig, float_field_schema, input_value, expected):
    v = SchemaValidator(
        cs.model_schema(
            cls=MyModel,
            schema=cs.model_fields_schema(fields={'x': cs.model_field(schema=float_field_schema)}),
            config=config,
        )
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output_dict = v.validate_python(input_value)
        assert output_dict == expected


@pytest.mark.parametrize(
    'config,input_str',
    (
        (CoreConfig(), 'type=string_type, input_value=123, input_type=int'),
        (CoreConfig(hide_input_in_errors=False), 'type=string_type, input_value=123, input_type=int'),
        (CoreConfig(hide_input_in_errors=True), 'type=string_type'),
    ),
)
def test_hide_input_in_errors(config, input_str):
    v = SchemaValidator(
        cs.model_schema(
            cls=MyModel, schema=cs.model_fields_schema(fields={'f': cs.model_field(schema=cs.str_schema())})
        ),
        config=config,
    )

    with pytest.raises(ValidationError, match=re.escape(f'Input should be a valid string [{input_str}]')):
        assert v.validate_python({'f': 123})


def test_cache_strings():
    v = SchemaValidator(cs.str_schema())
    assert 'cache_strings=True' in plain_repr(v)

    v = SchemaValidator(cs.str_schema(), config=CoreConfig(cache_strings=True))
    assert 'cache_strings=True' in plain_repr(v)

    v = SchemaValidator(cs.str_schema(), config=CoreConfig(cache_strings=False))
    assert 'cache_strings=False' in plain_repr(v)

    v = SchemaValidator(cs.str_schema(), config=CoreConfig(cache_strings='keys'))
    assert "cache_strings='keys'" in plain_repr(v)
