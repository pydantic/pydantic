import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


def test_simple():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}})

    assert v.validate_python({'field_a': 123, 'field_b': 1}) == (
        {'field_a': '123', 'field_b': 1},
        {'field_b', 'field_a'},
    )


def test_with_default():
    v = SchemaValidator(
        {'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int', 'default': 666}}}
    )

    assert v.validate_python({'field_a': 123}) == ({'field_a': '123', 'field_b': 666}, {'field_a'})
    assert v.validate_python({'field_a': 123, 'field_b': 1}) == (
        {'field_a': '123', 'field_b': 1},
        {'field_b', 'field_a'},
    )


def test_missing_error():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 123})
    assert (
        str(exc_info.value)
        == """\
1 validation error for Model
field_b
  Field required [kind=missing, input_value={'field_a': 123}, input_type=dict]"""
    )


def test_ignore_extra():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}})

    assert v.validate_python({'field_a': 123, 'field_b': 1, 'field_c': 123}) == (
        {'field_a': '123', 'field_b': 1},
        {'field_b', 'field_a'},
    )


def test_forbid_extra():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}, 'config': {'extra': 'forbid'}})

    with pytest.raises(ValidationError, match='field_b | Extra values are not permitted'):
        v.validate_python({'field_a': 123, 'field_b': 1})


def test_allow_extra():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}, 'config': {'extra': 'allow'}})

    assert v.validate_python({'field_a': 123, 'field_b': (1, 2)}) == (
        {'field_a': '123', 'field_b': (1, 2)},
        {'field_a', 'field_b'},
    )


def test_allow_extra_validate():
    v = SchemaValidator(
        {
            'type': 'model',
            'fields': {'field_a': {'type': 'str'}},
            'extra_validator': {'type': 'int'},
            'config': {'extra': 'allow'},
        }
    )

    assert v.validate_python({'field_a': 'test', 'other_value': '123'}) == (
        {'field_a': 'test', 'other_value': 123},
        {'field_a', 'other_value'},
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'test', 'other_value': 12.5})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_from_float',
            'loc': ['other_value'],
            'message': 'Value must be a valid integer, got a number with a fractional part',
            'input_value': 12.5,
        }
    ]


def test_str_config():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}, 'config': {'str_max_length': 5}})
    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    with pytest.raises(ValidationError, match='String must have at most 5 characters'):
        v.validate_python({'field_a': 'test long'})


def test_validate_assignment():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}})

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    assert v.validate_assignment('field_a', 456, {'field_a': 'test'}) == ({'field_a': '456'}, {'field_a'})


def test_validate_assignment_functions():
    calls = []

    def func_a(input_value, **kwargs):
        calls.append('func_a')
        return input_value * 2

    def func_b(input_value, **kwargs):
        calls.append('func_b')
        return input_value / 2

    v = SchemaValidator(
        {
            'type': 'model',
            'fields': {
                'field_a': {'type': 'function-after', 'function': func_a, 'field': {'type': 'str'}},
                'field_b': {'type': 'function-after', 'function': func_b, 'field': {'type': 'int'}},
            },
        }
    )

    assert v.validate_python({'field_a': 'test', 'field_b': 12.0}) == (
        {'field_a': 'testtest', 'field_b': 6},
        {'field_a', 'field_b'},
    )

    assert calls == ['func_a', 'func_b']
    calls.clear()

    assert v.validate_assignment('field_a', 'new-val', {'field_a': 'testtest', 'field_b': 6}) == (
        {'field_a': 'new-valnew-val', 'field_b': 6},
        {'field_a'},
    )
    assert calls == ['func_a']


def test_validate_assignment_ignore_extra():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}})

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment('other_field', 456, {'field_a': 'test'})

    assert exc_info.value.errors() == [
        {
            'kind': 'extra_forbidden',
            'loc': ['other_field'],
            'message': 'Extra values are not permitted',
            'input_value': 456,
        }
    ]


def test_validate_assignment_allow_extra():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}}, 'config': {'extra': 'allow'}})

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    assert v.validate_assignment('other_field', 456, {'field_a': 'test'}) == (
        {'field_a': 'test', 'other_field': 456},
        {'other_field'},
    )


def test_validate_assignment_allow_extra_validate():
    v = SchemaValidator(
        {
            'type': 'model',
            'fields': {'field_a': {'type': 'str'}},
            'extra_validator': {'type': 'int'},
            'config': {'extra': 'allow'},
        }
    )

    assert v.validate_assignment('other_field', '456', {'field_a': 'test'}) == (
        {'field_a': 'test', 'other_field': 456},
        {'other_field'},
    )
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_assignment('other_field', 'xyz', {'field_a': 'test'})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['other_field'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'xyz',
        }
    ]


def test_model_class():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model-class',
            'class': MyModel,
            'model': {'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}},
        }
    )
    assert repr(v).startswith('SchemaValidator(title="Model", validator=ModelClassValidator {\n')
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}
    assert m.__dict__ == {'field_a': 'test', 'field_b': 12}


def test_model_class_setattr():
    setattr_calls = []

    class MyModel:
        field_a: str

        def __setattr__(self, key, value):
            setattr_calls.append((key, value))
            # don't do anything

    m1 = MyModel()
    m1.foo = 'bar'
    assert not hasattr(m1, 'foo')
    assert setattr_calls == [('foo', 'bar')]
    setattr_calls.clear()

    v = SchemaValidator(
        {'type': 'model-class', 'class': MyModel, 'model': {'type': 'model', 'fields': {'field_a': {'type': 'str'}}}}
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, MyModel)
    # assert m.field_a == 'test'
    # assert m.__fields_set__ == {'field_a'}
    assert setattr_calls == []


def test_model_class_root_validator():
    class MyModel:
        pass

    def f(input_value, *, validator, **kwargs):
        output = validator(input_value)
        return str(output)

    v = SchemaValidator(
        {
            'title': 'Test',
            'type': 'function-wrap',
            'function': f,
            'field': {
                'type': 'model-class',
                'class': MyModel,
                'model': {'type': 'model', 'fields': {'field_a': {'type': 'str'}}},
            },
        }
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, str)
    assert 'test_model_class_root_validator.<locals>.MyModel' in m


def test_model_class_bad_model():
    class MyModel:
        pass

    with pytest.raises(SchemaError, match=re.escape("model-class expected a 'model' schema, got 'str'")):
        SchemaValidator({'type': 'model-class', 'class': MyModel, 'model': {'type': 'str'}})


def test_model_class_not_type():
    with pytest.raises(SchemaError, match=re.escape("TypeError: 'int' object cannot be converted to 'PyType'")):
        SchemaValidator({'type': 'model-class', 'class': 123})


def test_model_class_instance_direct():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init'

    v = SchemaValidator(
        {'type': 'model-class', 'class': MyModel, 'model': {'type': 'model', 'fields': {'field_a': {'type': 'str'}}}}
    )
    m1 = v.validate_python({'field_a': 'test'})
    assert isinstance(m1, MyModel)
    assert m1.field_a == 'test'
    assert m1.__fields_set__ == {'field_a'}

    m2 = MyModel()
    m3 = v.validate_python(m2)
    assert m2 == m3
    assert m3.field_a == 'init'


def test_model_class_instance_subclass():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init_a'

    class MySubModel(MyModel):
        field_b: str

        def __init__(self):
            super().__init__()
            self.field_b = 'init_b'

    v = SchemaValidator(
        {'type': 'model-class', 'class': MyModel, 'model': {'type': 'model', 'fields': {'field_a': {'type': 'str'}}}}
    )

    m2 = MySubModel()
    assert m2.field_a
    m3 = v.validate_python(m2)
    assert m2 != m3
    assert m3.field_a == 'init_a'
    assert not hasattr(m3, 'field_b')
