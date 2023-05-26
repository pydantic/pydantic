from dirty_equals import IsInstance

from pydantic_core import CoreConfig, SchemaValidator, core_schema


class MyModel:
    # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
    field_a: str
    field_b: int


def test_model_init():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                    'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
                },
            },
        }
    )
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b'}

    m2 = MyModel()
    ans = v.validate_python({'field_a': 'test', 'field_b': 12}, self_instance=m2)
    assert ans == m2
    assert ans.field_a == 'test'
    assert ans.field_b == 12
    assert ans.__pydantic_fields_set__ == {'field_a', 'field_b'}


def test_model_init_nested():
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                    'field_b': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'model',
                            'cls': MyModel,
                            'schema': {
                                'type': 'model-fields',
                                'fields': {
                                    'x_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                                    'x_b': {'type': 'model-field', 'schema': {'type': 'int'}},
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

    assert m2.__pydantic_fields_set__ == {'field_a', 'field_b'}


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
                    'type': 'model-fields',
                    'fields': {
                        'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
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
    assert m2.__pydantic_fields_set__ == {'field_a', 'field_b'}


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
                    'type': 'model-fields',
                    'fields': {
                        'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
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
    assert m2.__pydantic_fields_set__ == {'field_a', 'field_b'}


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
                    'type': 'model-fields',
                    'fields': {
                        'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
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
    assert m2.__pydantic_fields_set__ == {'field_a', 'field_b'}


def test_simple():
    v = SchemaValidator({'type': 'str'})
    assert v.validate_python(b'abc') == 'abc'
    assert v.isinstance_python(b'abc') is True

    assert v.validate_python(b'abc', self_instance='foobar') == 'abc'
    assert v.isinstance_python(b'abc', self_instance='foobar') is True

    assert v.validate_json('"abc"') == 'abc'

    assert v.validate_json('"abc"', self_instance='foobar') == 'abc'


def test_model_custom_init():
    calls = []

    class Model:
        def __init__(self, **kwargs):
            calls.append(repr(kwargs))
            if 'a' in kwargs:
                kwargs['a'] *= 2
            self.__pydantic_validator__.validate_python(kwargs, self_instance=self)
            self.c = self.a + 2

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=1)),
                    'b': core_schema.model_field(core_schema.int_schema()),
                }
            ),
            custom_init=True,
        )
    )
    Model.__pydantic_validator__ = v

    m = v.validate_python({'b': 2})
    assert m.a == 1
    assert m.b == 2
    assert m.c == 3
    assert m.__pydantic_fields_set__ == {'b'}
    assert calls == ["{'b': 2}"]

    m2 = v.validate_python({'a': 5, 'b': 3})
    assert m2.a == 10
    assert m2.b == 3
    assert m2.c == 12
    assert m2.__pydantic_fields_set__ == {'a', 'b'}
    assert calls == ["{'b': 2}", "{'a': 5, 'b': 3}"]

    m3 = v.validate_json('{"a":10, "b": 4}')
    assert m3.a == 20
    assert m3.b == 4
    assert m3.c == 22
    assert m3.__pydantic_fields_set__ == {'a', 'b'}
    assert calls == ["{'b': 2}", "{'a': 5, 'b': 3}", "{'a': 10, 'b': 4}"]


def test_model_custom_init_nested():
    calls = []

    class ModelInner:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int
        b: int

        def __init__(self, **data):
            calls.append(f'inner: {data!r}')
            self.__pydantic_validator__.validate_python(data, self_instance=self)

    inner_schema = core_schema.model_schema(
        ModelInner,
        core_schema.model_fields_schema(
            {
                'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=1)),
                'b': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        custom_init=True,
    )
    ModelInner.__pydantic_validator__ = SchemaValidator(inner_schema)

    class ModelOuter:
        __slots__ = '__dict__', '__pydantic_fields_set__'
        a: int
        b: ModelInner

        def __init__(self, **data):
            calls.append(f'outer: {data!r}')
            self.__pydantic_validator__.validate_python(data, self_instance=self)

    ModelOuter.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            ModelOuter,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=1)),
                    'b': core_schema.model_field(inner_schema),
                }
            ),
            custom_init=True,
        )
    )

    m = ModelOuter(a=2, b={'b': 3})
    assert m.__pydantic_fields_set__ == {'a', 'b'}
    assert m.a == 2
    assert isinstance(m.b, ModelInner)
    assert m.b.a == 1
    assert m.b.b == 3
    # insert_assert(calls)
    assert calls == ["outer: {'a': 2, 'b': {'b': 3}}", "inner: {'b': 3}"]


def test_model_custom_init_extra():
    calls = []

    class ModelInner:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int
        b: int

        def __getattr__(self, item):
            return self.__pydantic_extra__[item]

        def __init__(self, **data):
            self.__pydantic_validator__.validate_python(data, self_instance=self)
            calls.append(('inner', self.__dict__, self.__pydantic_fields_set__, self.__pydantic_extra__))

    inner_schema = core_schema.model_schema(
        ModelInner,
        core_schema.model_fields_schema(
            {
                'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=1)),
                'b': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        config=CoreConfig(extra_fields_behavior='allow'),
        custom_init=True,
    )
    ModelInner.__pydantic_validator__ = SchemaValidator(inner_schema)

    class ModelOuter:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int
        b: ModelInner

        def __getattr__(self, item):
            return self.__pydantic_extra__[item]

        def __init__(self, **data):
            data['b']['z'] = 1
            self.__pydantic_validator__.validate_python(data, self_instance=self)
            calls.append(('outer', self.__dict__, self.__pydantic_fields_set__, self.__pydantic_extra__))

    ModelOuter.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            ModelOuter,
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.with_default_schema(core_schema.int_schema(), default=1)),
                    'b': core_schema.model_field(inner_schema),
                }
            ),
            config=CoreConfig(extra_fields_behavior='allow'),
            custom_init=True,
        )
    )

    m = ModelOuter(a=2, b={'b': 3}, c=1)
    assert m.__pydantic_fields_set__ == {'a', 'b', 'c'}
    assert m.a == 2
    assert m.c == 1
    assert isinstance(m.b, ModelInner)
    assert m.b.a == 1
    assert m.b.b == 3
    assert m.b.z == 1
    # insert_assert(calls)
    assert calls == [
        ('inner', {'a': 1, 'b': 3}, {'b', 'z'}, {'z': 1}),
        ('outer', {'a': 2, 'b': IsInstance(ModelInner)}, {'c', 'a', 'b'}, {'c': 1}),
    ]


def test_model_custom_init_revalidate():
    calls = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

        def __init__(self, **kwargs):
            calls.append(repr(kwargs))
            self.__dict__.update(kwargs)
            self.__pydantic_fields_set__ = {'custom'}
            self.__pydantic_extra__ = None

    v = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            custom_init=True,
            config=dict(revalidate_instances='always'),
        )
    )

    m = v.validate_python({'a': '1'})
    assert isinstance(m, Model)
    assert m.a == '1'
    assert m.__pydantic_fields_set__ == {'custom'}
    assert calls == ["{'a': '1'}"]
    m.x = 4

    m2 = v.validate_python(m)
    assert m2 is not m
    assert isinstance(m2, Model)
    assert m2.a == '1'
    assert m2.__dict__ == {'a': '1', 'x': 4}
    assert m2.__pydantic_fields_set__ == {'custom'}
    assert calls == ["{'a': '1'}", "{'a': '1', 'x': 4}"]
