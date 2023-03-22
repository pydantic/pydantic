from pydantic_core import SchemaValidator


class MyModel:
    # this is not required, but it avoids `__fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__fields_set__'
    field_a: str
    field_b: int


def test_model_init():

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}

    m2 = MyModel()
    ans = v.validate_python({'field_a': 'test', 'field_b': 12}, self_instance=m2)
    assert ans == m2
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}


def test_model_init_nested():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {
                        'type': 'typed-dict-field',
                        'schema': {
                            'type': 'model',
                            'cls': MyModel,
                            'schema': {
                                'type': 'typed-dict',
                                'return_fields_set': True,
                                'fields': {
                                    'x_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                                    'x_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                                },
                            },
                        },
                    },
                },
            },
        }
    )
    m = v.validate_python({'field_a': 'test', 'field_b': {'x_a': 'foo', 'x_b': 12}})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert isinstance(m.field_b, MyModel)
    assert m.field_b.x_a == 'foo'
    assert m.field_b.x_b == 12

    m2 = MyModel()
    v.validate_python({'field_a': 'test', 'field_b': {'x_a': 'foo', 'x_b': 12}}, self_instance=m2)
    assert m2.field_a == 'test'
    assert isinstance(m2.field_b, MyModel)
    assert m2.field_b.x_a == 'foo'
    assert m2.field_b.x_b == 12

    assert m2.__fields_set__ == {'field_a', 'field_b'}


def test_function_before():
    def f(input_value, _info):
        assert isinstance(input_value, dict)
        input_value['field_a'] += b' XX'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function-before',
            'function': {'type': 'general', 'function': f},
            'schema': {
                'type': 'model',
                'cls': MyModel,
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {
                        'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                    },
                },
            },
        }
    )

    m = v.validate_python({'field_a': b'321', 'field_b': '12'})
    assert isinstance(m, MyModel)
    assert m.field_a == '321 XX'
    assert m.field_b == 12

    m2 = MyModel()
    v.validate_python({'field_a': b'321', 'field_b': '12'}, self_instance=m2)
    assert m2.__dict__ == {'field_a': '321 XX', 'field_b': 12}
    assert m2.__fields_set__ == {'field_a', 'field_b'}


def test_function_after():
    def f(input_value, _info):
        # always a model here, because even with `self_instance` the validator returns a model, e.g. m2 here
        assert isinstance(input_value, MyModel)
        input_value.field_a += ' Changed'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function-after',
            'function': {'type': 'general', 'function': f},
            'schema': {
                'type': 'model',
                'cls': MyModel,
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {
                        'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                    },
                },
            },
        }
    )

    m = v.validate_python({'field_a': b'321', 'field_b': '12'})
    assert isinstance(m, MyModel)
    assert m.field_a == '321 Changed'
    assert m.field_b == 12

    m2 = MyModel()
    v.validate_python({'field_a': b'321', 'field_b': '12'}, self_instance=m2)
    assert m2.__dict__ == {'field_a': '321 Changed', 'field_b': 12}
    assert m2.__fields_set__ == {'field_a', 'field_b'}


def test_function_wrap():
    def f(input_value, handler, _info):
        assert isinstance(input_value, dict)
        v = handler(input_value)
        # always a model here, because even with `self_instance` the validator returns a model, e.g. m2 here
        assert isinstance(v, MyModel)
        v.field_a += ' Changed'
        return v

    v = SchemaValidator(
        {
            'type': 'function-wrap',
            'function': {'type': 'general', 'function': f},
            'schema': {
                'type': 'model',
                'cls': MyModel,
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {
                        'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                    },
                },
            },
        }
    )

    m = v.validate_python({'field_a': b'321', 'field_b': '12'})
    assert isinstance(m, MyModel)
    assert m.field_a == '321 Changed'
    assert m.field_b == 12

    m2 = MyModel()
    v.validate_python({'field_a': b'321', 'field_b': '12'}, self_instance=m2)
    assert m2.__dict__ == {'field_a': '321 Changed', 'field_b': 12}
    assert m2.__fields_set__ == {'field_a', 'field_b'}


def test_simple():
    v = SchemaValidator({'type': 'str'})
    assert v.validate_python(b'abc') == 'abc'
    assert v.isinstance_python(b'abc') is True

    assert v.validate_python(b'abc', self_instance='foobar') == 'abc'
    assert v.isinstance_python(b'abc', self_instance='foobar') is True

    assert v.validate_json('"abc"') == 'abc'
    assert v.isinstance_json('"abc"') is True

    assert v.validate_json('"abc"', self_instance='foobar') == 'abc'
    assert v.isinstance_json('"abc"', self_instance='foobar') is True
