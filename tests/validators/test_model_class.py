import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


def test_model_class():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model-class',
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
            },
        }
    )
    assert repr(v).startswith('SchemaValidator(name="MyModel", validator=ModelClass(\n')
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
        {
            'type': 'model-class',
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'schema': {'type': 'str'}}},
            },
        }
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
            'type': 'function',
            'mode': 'wrap',
            'function': f,
            'schema': {
                'type': 'model-class',
                'class_type': MyModel,
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {'field_a': {'schema': {'type': 'str'}}},
                },
            },
        }
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, str)
    assert 'test_model_class_root_validator.<locals>.MyModel' in m


def test_model_class_bad_model():
    class MyModel:
        pass

    with pytest.raises(SchemaError, match=re.escape("model-class expected a 'typed-dict' schema, got 'str'")):
        SchemaValidator({'type': 'model-class', 'class_type': MyModel, 'schema': {'type': 'str'}})


def test_model_class_not_type():
    with pytest.raises(SchemaError, match=re.escape("TypeError: 'int' object cannot be converted to 'PyType'")):
        SchemaValidator({'type': 'model-class', 'class_type': 123})


def test_model_class_instance_direct():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init'

    v = SchemaValidator(
        {
            'type': 'model-class',
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'schema': {'type': 'str'}}},
            },
        }
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
        {
            'type': 'model-class',
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'schema': {'type': 'str'}}},
                'config': {'from_attributes': True},
            },
        }
    )

    m2 = MySubModel()
    assert m2.field_a
    m3 = v.validate_python(m2)
    assert m2 != m3
    assert m3.field_a == 'init_a'
    assert not hasattr(m3, 'field_b')


def test_model_class_strict():
    class MyModel:
        def __init__(self):
            self.field_a = 'init_a'
            self.field_b = 'init_b'

    v = SchemaValidator(
        {
            'type': 'model-class',
            'strict': True,
            'class_type': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
            },
        }
    )
    m = MyModel()
    m2 = v.validate_python(m)
    assert isinstance(m, MyModel)
    assert m is m2
    assert m.field_a == 'init_a'
    # note that since dict validation was not run here, there has been no check this is an int
    assert m.field_b == 'init_b'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'test', 'field_b': 12})
    assert exc_info.value.errors() == [
        {
            'kind': 'model_class_type',
            'loc': [],
            'message': 'Value must be an instance of MyModel',
            'input_value': {'field_a': 'test', 'field_b': 12},
            'context': {'class_name': 'MyModel'},
        }
    ]
    assert str(exc_info.value).startswith('1 validation error for MyModel\n')


def test_internal_error():
    v = SchemaValidator(
        {
            'type': 'model-class',
            'class_type': int,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': 'int'}}},
        }
    )
    with pytest.raises(AttributeError, match=re.escape("'int' object has no attribute '__dict__'")):
        v.validate_python({'f': 123})
