import re
from copy import deepcopy
from typing import Any, Callable, Dict, List, Set, Tuple

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
    assert m.field_a == 'test'
    assert m.__fields_set__ == {'field_a'}
    assert setattr_calls == []


def test_model_class_root_validator_wrap():
    class MyModel:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(
        input_value: Dict[str, Any],
        validator: Callable[[Dict[str, Any]], Dict[str, Any]],
        info: core_schema.ValidationInfo,
    ):
        assert input_value['field_a'] == 123
        output = validator(input_value)
        return output

    schema = core_schema.model_schema(
        MyModel,
        core_schema.general_wrap_validator_function(
            f,
            core_schema.typed_dict_schema(
                {'field_a': core_schema.typed_dict_field(core_schema.int_schema())}, return_fields_set=True
            ),
        ),
    )

    v = SchemaValidator(schema)
    m = v.validate_python({'field_a': 123})
    assert m.field_a == 123

    with pytest.raises(ValidationError) as e:
        v.validate_python({'field_a': 456})

    assert e.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, assert 456 == 123',
            'input': {'field_a': 456},
            'ctx': {'error': 'assert 456 == 123'},
        }
    ]


def test_model_class_root_validator_before():
    class MyModel:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value: Dict[str, Any], info: core_schema.ValidationInfo):
        assert input_value['field_a'] == 123
        return input_value

    schema = core_schema.model_schema(
        MyModel,
        core_schema.general_before_validator_function(
            f,
            core_schema.typed_dict_schema(
                {'field_a': core_schema.typed_dict_field(core_schema.int_schema())}, return_fields_set=True
            ),
        ),
    )

    v = SchemaValidator(schema)
    m = v.validate_python({'field_a': 123})
    assert m.field_a == 123

    with pytest.raises(ValidationError) as e:
        v.validate_python({'field_a': 456})

    assert e.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, assert 456 == 123',
            'input': {'field_a': 456},
            'ctx': {'error': 'assert 456 == 123'},
        }
    ]


def test_model_class_root_validator_after():
    class MyModel:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    def f(input_value_and_fields_set: Tuple[Dict[str, Any], Set[str]], info: core_schema.ValidationInfo):
        input_value, _ = input_value_and_fields_set
        assert input_value['field_a'] == 123
        return input_value_and_fields_set

    schema = core_schema.model_schema(
        MyModel,
        core_schema.general_after_validator_function(
            f,
            core_schema.typed_dict_schema(
                {'field_a': core_schema.typed_dict_field(core_schema.int_schema())}, return_fields_set=True
            ),
        ),
    )

    v = SchemaValidator(schema)
    m = v.validate_python({'field_a': 123})
    assert m.field_a == 123

    with pytest.raises(ValidationError) as e:
        v.validate_python({'field_a': 456})

    assert e.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, assert 456 == 123',
            'input': {'field_a': 456},
            'ctx': {'error': 'assert 456 == 123'},
        }
    ]


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
    post_init_calls = []

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init_a'

        def model_post_init(self, context):
            post_init_calls.append(context)

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
            'post_init': 'model_post_init',
        }
    )

    m2 = MySubModel()
    assert m2.field_a
    m3 = v.validate_python(m2, context='call1')
    assert m2 is m3
    assert m3.field_a == 'init_a'
    assert m3.field_b == 'init_b'
    assert post_init_calls == []

    m4 = v.validate_python({'field_a': b'hello'}, context='call2')
    assert isinstance(m4, MyModel)
    assert m4.field_a == 'hello'
    assert m4.__fields_set__ == {'field_a'}
    assert post_init_calls == ['call2']


def test_model_class_instance_subclass_revalidate():
    post_init_calls = []

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str

        def __init__(self):
            self.field_a = 'init_a'

        def model_post_init(self, context):
            post_init_calls.append(context)

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
            'post_init': 'model_post_init',
            'revalidate_instances': 'always',
        }
    )

    m2 = MySubModel()
    assert m2.field_a
    m3 = v.validate_python(m2, context='call1')
    assert m2 is not m3
    assert m3.field_a == 'init_a'
    assert not hasattr(m3, 'field_b')
    assert post_init_calls == ['call1']

    m4 = MySubModel()
    m4.__fields_set__ = {'fruit_loop'}
    m5 = v.validate_python(m4, context='call2')
    assert m4 is not m5
    assert m5.__fields_set__ == {'fruit_loop'}
    assert m5.field_a == 'init_a'
    assert not hasattr(m5, 'field_b')
    assert post_init_calls == ['call1', 'call2']


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
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: Never'
    m = MyModel()
    m2 = v.validate_python(m)
    assert isinstance(m, MyModel)
    assert m is m2
    assert m.field_a == 'init_a'
    # note that since dict validation was not run here, there has been no check this is an int
    assert m.field_b == 'init_b'
    with pytest.raises(ValidationError, match='^1 validation error for MyModel\n') as exc_info:
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

    class MySubModel(MyModel):
        field_c: str

        def __init__(self):
            super().__init__()
            self.field_c = 'init_c'

    # instances of subclasses are allowed in strict mode
    m3 = MySubModel()
    m4 = v.validate_python(m3)
    assert m4 is m3


def test_model_class_strict_json():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int
        field_c: int

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
                    'field_c': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'default': 42, 'schema': {'type': 'int'}},
                    },
                },
            },
        }
    )
    m = v.validate_json('{"field_a": "foobar", "field_b": "123"}')
    assert isinstance(m, MyModel)
    assert m.field_a == 'foobar'
    assert m.field_b == 123
    assert m.field_c == 42
    assert m.__fields_set__ == {'field_a', 'field_b'}


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


def test_revalidate_always():
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
            'revalidate_instances': 'always',
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'from_attributes': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: Always'

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


def test_revalidate_subclass_instances():
    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

        def __init__(self):
            self.field_a = 'init_a'
            self.field_b = 123

    class MySubModel(MyModel):
        def __init__(self):
            super().__init__()
            self.field_c = 'init_c'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'revalidate_instances': 'subclass-instances',
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'from_attributes': True,
                'fields': {
                    'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )

    m1 = MyModel()
    m2 = v.validate_python(m1)
    assert m2 is m1

    m3 = MySubModel()
    assert hasattr(m3, 'field_c')
    m4 = v.validate_python(m3)
    assert m4 is not m3
    assert type(m4) is MyModel
    assert not hasattr(m4, 'field_c')

    m5 = MySubModel()
    m5.field_b = 'not an int'
    with pytest.raises(ValidationError, match="type=int_parsing, input_value='not an int', input_type=str"):
        v.validate_python(m5)


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
            'config': {'revalidate_instances': 'always'},
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
            'config': {'revalidate_instances': 'always'},
        }
    )
    assert re.search(r'revalidate: \w+', repr(v)).group(0) == 'revalidate: Always'

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

    calls: List[Any] = []

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
    with pytest.raises(AttributeError, match="'str' object has no attribute '__dict__'"):
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


@pytest.mark.parametrize(
    'function_schema,call1, call2',
    [
        (
            core_schema.general_after_validator_function,
            (({'a': 1, 'b': 2}, {'b'}), 'ValidationInfo(config=None, context=None)'),
            (({'a': 10, 'b': 2}, {'a'}), 'ValidationInfo(config=None, context=None)'),
        ),
        (
            core_schema.general_before_validator_function,
            ({'b': 2}, 'ValidationInfo(config=None, context=None)'),
            ({'a': 10, 'b': 2}, 'ValidationInfo(config=None, context=None)'),
        ),
        (
            core_schema.general_wrap_validator_function,
            ({'b': 2}, 'ValidationInfo(config=None, context=None)'),
            ({'a': 10, 'b': 2}, 'ValidationInfo(config=None, context=None)'),
        ),
    ],
)
def test_validate_assignment_model_validator_function(function_schema: Any, call1: Any, call2: Any):
    """
    Test handling of values and fields_set for validator functions that wrap a model when using
    validate_assignment.

    Note that we are currently not exposing this functionality in conjunction with getting
    access to `fields_set` in a model validator, so the behavior of fields set.
    In particular, for function_after it is not clear if the fields set passed to
    the validator should be the fields that were assigned on this call to `validate_assignment`
    (currently always a single field) or the fields that have been assigned in the
    model since it was created.
    """

    class Model:
        __slots__ = ('__dict__', '__fields_set__')

    calls: List[Any] = []

    def f(values_or_values_and_fields_set: Any, *args: Any) -> Any:
        if len(args) == 2:
            # wrap
            handler, info = args
            calls.append((deepcopy(values_or_values_and_fields_set), str(info)))
            return handler(values_or_values_and_fields_set)
        else:
            info = args[0]
            calls.append((deepcopy(values_or_values_and_fields_set), str(info)))
            return values_or_values_and_fields_set

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            function_schema(
                f,
                core_schema.typed_dict_schema(
                    {
                        'a': core_schema.typed_dict_field(
                            core_schema.with_default_schema(core_schema.int_schema(), default=1)
                        ),
                        'b': core_schema.typed_dict_field(core_schema.int_schema()),
                    },
                    return_fields_set=True,
                ),
            ),
        )
    )

    m = v.validate_python({'b': 2})
    assert m.a == 1
    assert m.b == 2
    assert m.__fields_set__ == {'b'}
    assert calls == [call1]

    v.validate_assignment(m, 'a', 10)
    assert m.a == 10
    assert m.b == 2
    assert m.__fields_set__ == {'a', 'b'}
    assert calls == [call1, call2]
