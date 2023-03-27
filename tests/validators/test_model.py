import re

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import plain_repr


def test_model_class():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

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
    assert 'expect_fields_set:true' in plain_repr(v)
    assert repr(v).startswith('SchemaValidator(title="MyModel", validator=Model(\n')
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}
    assert m.__dict__ == {'field_a': 'test', 'field_b': 12}

    with pytest.raises(ValidationError, match='Input should be an instance of MyModel') as exc_info:
        v.validate_python({'field_a': 'test', 'field_b': 12}, strict=True)

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'model_class_type',
            'loc': (),
            'msg': 'Input should be an instance of MyModel',
            'input': {'field_a': 'test', 'field_b': 12},
            'ctx': {'class_name': 'MyModel'},
        }
    ]


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
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
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

    def f(input_value, validator, info):
        output = validator(input_value)
        return str(output)

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
                    'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
                },
            },
        }
    )
    assert 'expect_fields_set:true' in plain_repr(v)
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, str)
    assert 'test_model_class_root_validator.<locals>.MyModel' in m


@pytest.mark.parametrize('mode', ['before', 'after', 'wrap'])
@pytest.mark.parametrize('return_fields_set', [True, False])
def test_function_ask(mode, return_fields_set):
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

    def f(input_value, info):
        return input_value

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': f'function-{mode}',
                'function': {'type': 'general', 'function': f},
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': return_fields_set,
                    'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
                },
            },
        }
    )
    expect_fields_set = re.search('expect_fields_set:(true|false)', plain_repr(v)).group(1)
    assert expect_fields_set == str(return_fields_set).lower()


def test_function_plain_ask():
    class MyModel:
        pass

    def f(input_value, info):
        return input_value

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {'type': 'function-plain', 'function': {'type': 'general', 'function': f}},
        }
    )
    assert 'expect_fields_set:false' in plain_repr(v)
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test'}
    assert not hasattr(m, '__fields_set__')


def test_union_sub_schema():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'union',
                'choices': [
                    {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {'foo': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
                    },
                    {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {'bar': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
                    },
                ],
            },
        }
    )
    assert 'expect_fields_set:true' in plain_repr(v)
    m = v.validate_python({'foo': '123'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'foo': 123}
    assert m.__fields_set__ == {'foo'}
    m = v.validate_python({'bar': '123'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'bar': 123}
    assert m.__fields_set__ == {'bar'}


def test_tagged_union_sub_schema():
    class MyModel:
        pass

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'tagged-union',
                'discriminator': 'foo',
                'choices': {
                    'apple': {
                        'type': 'typed-dict',
                        'fields': {
                            'foo': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                            'bar': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                        },
                    },
                    'banana': {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {
                            'foo': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                            'spam': {
                                'type': 'typed-dict-field',
                                'schema': {'type': 'list', 'items_schema': {'type': 'int'}},
                            },
                        },
                    },
                },
            },
        }
    )
    assert 'expect_fields_set:false' in plain_repr(v)  # because only one choice has return_fields_set=True!
    m = v.validate_python({'foo': 'apple', 'bar': '123'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'foo': 'apple', 'bar': 123}
    assert not hasattr(m, '__fields_set__')
    # error because banana has return_fields_set=True
    # "__dict__ must be set to a dictionary, not a 'tuple'" on cpython, different on pypy
    with pytest.raises(TypeError):
        v.validate_python({'foo': 'banana', 'spam': [1, 2, 3]})


def test_bad_sub_schema():
    class MyModel:
        pass

    v = SchemaValidator({'type': 'model', 'cls': MyModel, 'schema': {'type': 'int'}})
    assert 'expect_fields_set:false' in plain_repr(v)
    with pytest.raises(TypeError):
        v.validate_python(123)


def test_model_class_function_after():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

    def f(input_value, info):
        input_value[0]['x'] = 'y'
        return input_value

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'function-after',
                'function': {'type': 'general', 'function': f},
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
                },
            },
        }
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test', 'x': 'y'}
    assert m.__fields_set__ == {'field_a'}


def test_model_class_not_type():
    with pytest.raises(SchemaError, match=re.escape("TypeError: 'int' object cannot be converted to 'PyType'")):
        SchemaValidator(
            {
                'type': 'model',
                'cls': 123,
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
                },
            }
        )


def test_not_return_fields_set():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            },
        }
    )
    assert 'expect_fields_set:false' in plain_repr(v)

    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test'}
    assert not hasattr(m, '__fields_set__')


def test_model_class_instance_direct():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
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
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            },
            'config': {'from_attributes': True},
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
            'type': 'model',
            'strict': True,
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
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: false'
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
            'type': 'model_class_type',
            'loc': (),
            'msg': 'Input should be an instance of MyModel',
            'input': {'field_a': 'test', 'field_b': 12},
            'ctx': {'class_name': 'MyModel'},
        }
    ]
    assert str(exc_info.value).startswith('1 validation error for MyModel\n')


def test_internal_error():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': int,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'f': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
            },
        }
    )
    with pytest.raises(AttributeError, match=re.escape("'int' object has no attribute '__dict__'")):
        v.validate_python({'f': 123})


def test_revalidate():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

        def __init__(self, a, b, fields_set):
            self.field_a = a
            self.field_b = b
            if fields_set is not None:
                self.__fields_set__ = fields_set

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'from_attributes': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
            'config': {'revalidate_models': True},
        }
    )
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: true'

    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test', 'field_b': 12}
    assert m.__fields_set__ == {'field_a', 'field_b'}

    m2 = MyModel('x', 42, {'field_a'})
    m3 = v.validate_python(m2)
    assert isinstance(m3, MyModel)
    assert m3 is not m2
    assert m3.__dict__ == {'field_a': 'x', 'field_b': 42}
    assert m3.__fields_set__ == {'field_a'}

    m4 = MyModel('x', 'not int', {'field_a'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(m4)
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('field_b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not int',
        }
    ]

    m5 = MyModel('x', 5, None)
    m6 = v.validate_python(m5)
    assert isinstance(m6, MyModel)
    assert m6 is not m5
    assert m6.__dict__ == {'field_a': 'x', 'field_b': 5}
    assert m6.__fields_set__ == {'field_a', 'field_b'}


def test_revalidate_extra():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'from_attributes': True,
                'extra_behavior': 'allow',
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
            'config': {'revalidate_models': True},
        }
    )

    m = v.validate_python({'field_a': 'test', 'field_b': 12, 'more': (1, 2, 3)})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test', 'field_b': 12, 'more': (1, 2, 3)}
    assert m.__fields_set__ == {'field_a', 'field_b', 'more'}

    m2 = MyModel(field_a='x', field_b=42, another=42.5)
    m3 = v.validate_python(m2)
    assert isinstance(m3, MyModel)
    assert m3 is not m2
    assert m3.__dict__ == {'field_a': 'x', 'field_b': 42, 'another': 42.5}
    assert m3.__fields_set__ == {'field_a', 'field_b', 'another'}


def test_post_init():
    call_count = 0

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

        def call_me_maybe(self, *args):
            nonlocal call_count
            call_count += 1
            assert len(args) == 1
            context = args[0]
            assert context is None
            assert self.field_a == 'test'
            assert self.field_b == 12
            assert self.__fields_set__ == {'field_a', 'field_b'}

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'post_init': 'call_me_maybe',
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
    assert call_count == 1


def test_revalidate_post_init():
    call_count = 0

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

        def call_me_maybe(self, context):
            nonlocal call_count
            call_count += 1
            assert context is None

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'post_init': 'call_me_maybe',
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'from_attributes': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
            'config': {'revalidate_models': True},
        }
    )
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: true'

    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': 'test', 'field_b': 12}
    assert m.__fields_set__ == {'field_a', 'field_b'}
    assert call_count == 1

    m2 = MyModel()
    m2.field_a = 'x'
    m2.field_b = 42
    m2.__fields_set__ = {'field_a'}

    m3 = v.validate_python(m2)
    assert isinstance(m3, MyModel)
    assert m3 is not m2
    assert m3.__dict__ == {'field_a': 'x', 'field_b': 42}
    assert m3.__fields_set__ == {'field_a'}
    assert call_count == 2


def test_post_init_validation_error():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def call_me_maybe(self, context, **kwargs):
            if context and 'error' in context:
                raise ValueError(f'this is broken: {self.field_a}')

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'post_init': 'call_me_maybe',
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            },
        }
    )
    m = v.validate_python({'field_a': 'test'})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'test'}, strict=None, context={'error': 1})
    assert exc_info.value.errors() == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, this is broken: test',
            'input': {'field_a': 'test'},
            'ctx': {'error': 'this is broken: test'},
        }
    ]


def test_post_init_internal_error():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def wrong_signature(self):
            pass

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'post_init': 'wrong_signature',
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            },
        }
    )
    with pytest.raises(TypeError, match=r'wrong_signature\(\) takes 1 positional argument but 2 were given'):
        v.validate_python({'field_a': 'test'})


def test_post_init_mutate():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

        def call_me_maybe(self, context, **kwargs):
            self.field_a *= 2
            self.__fields_set__ = {'field_a'}

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'post_init': 'call_me_maybe',
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
    assert m.field_a == 'testtest'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a'}
    assert m.__dict__ == {'field_a': 'testtest', 'field_b': 12}


def test_validate_assignment():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

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

    m = MyModel()
    m.field_a = 'hello'
    m.field_b = 123
    m.__fields_set__ = {'field_a'}

    v.validate_assignment(m, 'field_b', '321')

    m.field_a = 'hello'
    assert m.field_b == 321
    assert m.__fields_set__ == {'field_a', 'field_b'}


def test_validate_assignment_function():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int
        field_c: int

    calls = []

    def func(x, info):
        calls.append(str(info))
        return x * 2

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.typed_dict_schema(
                {
                    'field_a': core_schema.typed_dict_field(core_schema.str_schema()),
                    'field_b': core_schema.typed_dict_field(
                        core_schema.field_after_validator_function(func, core_schema.int_schema())
                    ),
                    'field_c': core_schema.typed_dict_field(core_schema.int_schema()),
                },
                return_fields_set=True,
            ),
        )
    )

    m = v.validate_python({'field_a': 'x', 'field_b': 123, 'field_c': 456})
    assert m.field_a == 'x'
    assert m.field_b == 246
    assert m.field_c == 456
    assert m.__fields_set__ == {'field_a', 'field_b', 'field_c'}
    assert calls == ["ValidationInfo(config=None, context=None, data={'field_a': 'x'}, field_name='field_b')"]

    v.validate_assignment(m, 'field_b', '111')

    assert m.field_b == 222
    assert calls == [
        "ValidationInfo(config=None, context=None, data={'field_a': 'x'}, field_name='field_b')",
        "ValidationInfo(config=None, context=None, data={'field_a': 'x', 'field_c': 456}, field_name='field_b')",
    ]


def test_validate_assignment_no_fields_set():
    class MyModel:
        __slots__ = ('__dict__',)

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

    m = MyModel()
    m.field_a = 'hello'
    m.field_b = 123
    assert not hasattr(m, '__fields_set__')

    v.validate_assignment(m, 'field_a', b'different')

    m.field_a = 'different'
    assert m.field_b == 123
    assert not hasattr(m, '__fields_set__')

    # wrong arguments
    with pytest.raises(TypeError, match='self_instance should not be None on typed-dict validate_assignment'):
        v.validate_assignment('field_a', 'field_a', b'different')


def test_frozen():
    class MyModel:
        __slots__ = {'__dict__'}

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.typed_dict_schema({'f': core_schema.typed_dict_field(core_schema.str_schema())}),
            frozen=True,
        )
    )

    m = v.validate_python({'f': 'x'})
    assert m.f == 'x'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'f', 'y')

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'frozen_instance', 'loc': (), 'msg': 'Instance is frozen', 'input': 'y'}
    ]
