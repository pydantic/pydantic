import math
import re

import pytest
from dirty_equals import FunctionCheck, HasAttributes, IsInstance

from pydantic_core import CoreConfig, SchemaValidator, ValidationError

from .conftest import Err, plain_repr


def test_on_field():
    v = SchemaValidator({'type': 'str', 'min_length': 2, 'max_length': 5})
    r = plain_repr(v)
    assert 'min_length:Some(2)' in r
    assert 'max_length:Some(5)' in r
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


def test_on_config():
    v = SchemaValidator({'type': 'str'}, {'str_max_length': 5})
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


def test_field_priority_arg():
    v = SchemaValidator({'type': 'str', 'max_length': 5}, {'str_max_length': 10})
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python('test') is True
    assert v.isinstance_python('test long') is False


class MyModel:
    # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def test_on_model_class():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'config': {'str_max_length': 5},
            'schema': {'type': 'model-fields', 'fields': {'f': {'type': 'model-field', 'schema': {'type': 'str'}}}},
        }
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_field_priority_model():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'config': {'str_max_length': 10},
            'schema': {
                'type': 'model-fields',
                'fields': {'f': {'type': 'model-field', 'schema': {'type': 'str', 'max_length': 5}}},
            },
        }
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


@pytest.mark.parametrize(
    'config,float_field_schema,input_value,expected',
    [
        ({}, {'type': 'float'}, {'x': 'nan'}, IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan))),
        (
            {'allow_inf_nan': True},
            {'type': 'float'},
            {'x': 'nan'},
            IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan)),
        ),
        (
            {'allow_inf_nan': False},
            {'type': 'float'},
            {'x': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
        # field `allow_inf_nan` (if set) should have priority over global config
        (
            {'allow_inf_nan': True},
            {'type': 'float', 'allow_inf_nan': False},
            {'x': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
        (
            {'allow_inf_nan': False},
            {'type': 'float', 'allow_inf_nan': True},
            {'x': 'nan'},
            IsInstance(MyModel) & HasAttributes(x=FunctionCheck(math.isnan)),
        ),
    ],
    ids=repr,
)
def test_allow_inf_nan(config: CoreConfig, float_field_schema, input_value, expected):
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {'type': 'model-fields', 'fields': {'x': {'type': 'model-field', 'schema': float_field_schema}}},
            'config': config,
        }
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
        ({}, 'type=string_type, input_value=123, input_type=int'),
        ({'hide_input_in_errors': False}, 'type=string_type, input_value=123, input_type=int'),
        ({'hide_input_in_errors': True}, 'type=string_type'),
    ),
)
def test_hide_input_in_errors(config, input_str):
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {'type': 'model-fields', 'fields': {'f': {'type': 'model-field', 'schema': {'type': 'str'}}}},
        },
        config,
    )

    with pytest.raises(ValidationError, match=re.escape(f'Input should be a valid string [{input_str}]')):
        assert v.validate_python({'f': 123})
