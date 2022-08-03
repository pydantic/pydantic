import pytest
from dirty_equals import HasAttributes, IsInstance

from pydantic_core import SchemaValidator, ValidationError

from .conftest import plain_repr


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
    # this is not required, but it avoids `__fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__fields_set__'


def test_on_model_class():

    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'config': {'str_max_length': 5},
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'str'}}},
        }
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_field_priority_model():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'config': {'str_max_length': 10},
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'f': {'schema': {'type': 'str', 'max_length': 5}}},
            },
        }
    )
    assert 'max_length:Some(5)' in plain_repr(v)
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_parent_priority():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'str'}}},
            'config': {'str_min_length': 2, 'str_max_length': 10},
        },
        {'str_max_length': 5, 'config_choose_priority': 1},
    )
    r = plain_repr(v)
    assert 'min_length:Some(2)' not in r  # child is ignored
    assert 'max_length:Some(5)' in r
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 't'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_child_priority():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'str'}}},
            'config': {'str_max_length': 5, 'config_choose_priority': 1},
        },
        {'str_min_length': 2, 'str_max_length': 10},
    )
    r = plain_repr(v)
    assert 'min_length:Some(2)' not in r  # parent is ignored
    assert 'max_length:Some(5)' in r
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 't'}) is True
    assert v.isinstance_python({'f': 'test long'}) is False


def test_merge_child_wins():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'str'}}},
            'config': {'str_max_length': 5},
        },
        {'str_min_length': 2, 'str_max_length': 10},
    )
    r = plain_repr(v)
    assert 'min_length:Some(2)' in r
    assert 'max_length:Some(5)' in r
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 't'}) is False
    assert v.isinstance_python({'f': 'test long'}) is False


def test_merge_parent_wins():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'str'}}},
            'config': {'str_max_length': 5},
        },
        {'str_min_length': 2, 'str_max_length': 10, 'config_merge_priority': 1},
    )
    r = plain_repr(v)
    assert 'min_length:Some(2)' in r
    assert 'max_length:Some(10)' in r
    assert 'max_length:Some(5)' not in r
    assert v.isinstance_python({'f': 'test'}) is True
    assert v.isinstance_python({'f': 't'}) is False
    assert v.isinstance_python({'f': 'test long'}) is True
    assert v.isinstance_python({'f': 'test very long'}) is False


def test_sub_model_merge():
    v = SchemaValidator(
        {
            'type': 'new-class',
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {
                    'f': {'schema': 'str'},
                    'sub_model': {
                        'schema': {
                            'type': 'new-class',
                            'class_type': MyModel,
                            'schema': {
                                'type': 'typed-dict',
                                'return_fields_set': True,
                                'fields': {'f': {'schema': 'str'}},
                            },
                            'config': {'str_max_length': 6, 'str_to_upper': True},
                        }
                    },
                },
            },
            'config': {'str_min_length': 1, 'str_max_length': 4},
        }
    )
    # f should have bounds 1-4
    # sub_model.f should have bounds 1-6, and should be upper-cased
    output = v.validate_python({'f': 'test', 'sub_model': {'f': 'tests'}})
    assert output == IsInstance(MyModel) & HasAttributes(f='test', sub_model=HasAttributes(f='TESTS'))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'f': 'tests', 'sub_model': {'f': ''}})
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': ['f'],
            'message': 'String should have at most 4 characters',
            'input_value': 'tests',
            'context': {'max_length': 4},
        },
        {
            'kind': 'too_short',
            'loc': ['sub_model', 'f'],
            'message': 'String should have at least 1 characters',
            'input_value': '',
            'context': {'min_length': 1},
        },
    ]
