import platform
import weakref

import pytest
from dirty_equals import IsInstance

from pydantic_core import CoreConfig, SchemaValidator, core_schema

from ..conftest import assert_gc


class MyModel:
    # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
    field_a: str
    field_b: int


def test_model_init():
    v = SchemaValidator(
        core_schema.model_schema(
            cls=MyModel,
            schema=core_schema.model_fields_schema(
                fields={
                    'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                    'field_b': core_schema.model_field(schema=core_schema.int_schema()),
                }
            ),
        )
    )
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b'}

    m2 = MyModel()
    validated = v.validate_python({'field_a': 'test', 'field_b': 12}, self_instance=m2)
    assert validated == m2
    assert validated.field_a == 'test'
    assert validated.field_b == 12
    assert validated.__pydantic_fields_set__ == {'field_a', 'field_b'}


def test_model_init_nested():
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    v = SchemaValidator(
        core_schema.model_schema(
            cls=MyModel,
            schema=core_schema.model_fields_schema(
                fields={
                    'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                    'field_b': core_schema.model_field(
                        schema=core_schema.model_schema(
                            cls=MyModel,
                            schema=core_schema.model_fields_schema(
                                fields={
                                    'x_a': core_schema.model_field(schema=core_schema.str_schema()),
                                    'x_b': core_schema.model_field(schema=core_schema.int_schema()),
                                }
                            ),
                        )
                    ),
                }
            ),
        )
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
            'function': {'type': 'with-info', 'function': f},
            'schema': core_schema.model_schema(
                cls=MyModel,
                schema=core_schema.model_fields_schema(
                    fields={
                        'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                        'field_b': core_schema.model_field(schema=core_schema.int_schema()),
                    }
                ),
            ),
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
            'function': {'type': 'with-info', 'function': f},
            'schema': core_schema.model_schema(
                cls=MyModel,
                schema=core_schema.model_fields_schema(
                    fields={
                        'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                        'field_b': core_schema.model_field(schema=core_schema.int_schema()),
                    }
                ),
            ),
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
            'function': {'type': 'with-info', 'function': f},
            'schema': core_schema.model_schema(
                cls=MyModel,
                schema=core_schema.model_fields_schema(
                    fields={
                        'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                        'field_b': core_schema.model_field(schema=core_schema.int_schema()),
                    }
                ),
            ),
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
    v = SchemaValidator(core_schema.str_schema())
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


def test_model_custom_init_with_after_model_validator_runs_once():
    """https://github.com/pydantic/pydantic/issues/13471

    Outer (`model_validators`) validators used to run twice on a `custom_init` model: once before
    `validate_construct` bounced validation through `__init__`, and once again on the resumed
    `self_instance` pass. They should run exactly once, for both direct construction and
    `validate_python`.
    """
    calls = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int

        def __init__(self, **kwargs):
            self.__pydantic_validator__.validate_python(kwargs, self_instance=self)

    def after_validator(m, info):
        calls.append('after')
        return m

    Model.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            custom_init=True,
            model_validators=[{'type': 'after', 'function': {'type': 'with-info', 'function': after_validator}}],
        )
    )

    m = Model(a=1)
    assert calls == ['after']
    assert m.a == 1

    calls.clear()
    Model.__pydantic_validator__.validate_python({'a': 2})
    assert calls == ['after']


def test_model_custom_init_with_wrap_model_validator_runs_once():
    """https://github.com/pydantic/pydantic/issues/13471 - `mode="wrap"` variant."""
    calls = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int

        def __init__(self, **kwargs):
            self.__pydantic_validator__.validate_python(kwargs, self_instance=self)

    def wrap_validator(value, handler, info):
        calls.append('before')
        result = handler(value)
        calls.append('after')
        return result

    Model.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            custom_init=True,
            model_validators=[{'type': 'wrap', 'function': {'type': 'with-info', 'function': wrap_validator}}],
        )
    )

    m = Model(a=1)
    assert calls == ['before', 'after']
    assert m.a == 1

    calls.clear()
    Model.__pydantic_validator__.validate_python({'a': 2})
    assert calls == ['before', 'after']


def test_model_custom_init_nested_with_after_model_validator_runs_once():
    """Nested-field variant of the fix in https://github.com/pydantic/pydantic/issues/13471."""
    calls = []

    class ModelInner:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int

        def __init__(self, **data):
            self.__pydantic_validator__.validate_python(data, self_instance=self)

    def after_validator(m, info):
        calls.append('inner')
        return m

    inner_schema = core_schema.model_schema(
        ModelInner,
        core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
        custom_init=True,
        model_validators=[{'type': 'after', 'function': {'type': 'with-info', 'function': after_validator}}],
    )
    ModelInner.__pydantic_validator__ = SchemaValidator(inner_schema)

    class ModelOuter:
        __slots__ = '__dict__', '__pydantic_fields_set__'
        b: ModelInner

        def __init__(self, **data):
            self.__pydantic_validator__.validate_python(data, self_instance=self)

    ModelOuter.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            ModelOuter,
            core_schema.model_fields_schema({'b': core_schema.model_field(inner_schema)}),
            custom_init=True,
        )
    )

    m = ModelOuter(b={'a': 1})
    assert calls == ['inner']
    assert m.b.a == 1


def test_model_custom_init_wrap_model_validator_revalidates_different_instance():
    """Regression test for a follow-up bug introduced while fixing
    https://github.com/pydantic/pydantic/issues/13471.

    A `mode="wrap"` model validator's `handler` can be called with a value other than the model's
    own input - including an *existing instance* of the model that needs revalidating. For a
    `custom_init` model with `revalidate_instances='always'`, this used to work (pre-#13471-fix)
    because `ModelValidator::validate` always extracted `__dict__` from an existing instance before
    handing it to `validate_construct`, regardless of how it was reached. After the #13471 fix moved
    that extraction into `ModelValidator`'s own (`self_instance=None`-only) code path, a `handler`
    call landing in `ModelInstanceBuilder`'s `self_instance=Some` branch (the *only* branch a
    `mode="wrap"` validator's `handler` can reach for a `custom_init` model, since outer model
    validators now only run during that resumed pass) received the raw instance directly and failed
    with a `model_type` error instead of revalidating it.
    """
    calls = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int

        def __init__(self, **kwargs):
            calls.append(('init', dict(kwargs)))
            self.__pydantic_validator__.validate_python(kwargs, self_instance=self)

    built_once = {'v': False}

    def wrap_validator(value, handler, info):
        calls.append(('wrap-before', type(value).__name__))
        if isinstance(value, dict) and not built_once['v']:
            built_once['v'] = True
            # a different, already-existing instance that needs revalidation (not the raw `value`
            # this validator itself was called with)
            other = Model.__new__(Model)
            object.__setattr__(other, '__dict__', {'a': 999})
            object.__setattr__(other, '__pydantic_fields_set__', {'a'})
            object.__setattr__(other, '__pydantic_extra__', None)
            object.__setattr__(other, '__pydantic_private__', None)
            result = handler(other)
        else:
            result = handler(value)
        calls.append(('wrap-after', result.a))
        return result

    Model.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            custom_init=True,
            config=CoreConfig(revalidate_instances='always'),
            model_validators=[{'type': 'wrap', 'function': {'type': 'with-info', 'function': wrap_validator}}],
        )
    )

    m = Model(a=1)
    assert m.a == 999
    # the wrap validator itself still runs exactly once (the #13471 fix stays intact)
    assert calls == [('init', {'a': 1}), ('wrap-before', 'dict'), ('wrap-after', 999)]


def test_model_wrap_model_validator_revalidates_different_instance_no_custom_init():
    """Second confirmed regression from the same fix as
    `test_model_custom_init_wrap_model_validator_revalidates_different_instance`, found during
    final review: a *non*-`custom_init` model has the identical bug in the `self_instance=None`
    branch of `ModelInstanceBuilder::validate` (specifically its `NotAnInstance`/`NeedsRevalidation`
    fallthrough) - this is a genuinely different code path from the `custom_init` case (that one is
    only ever reachable via the `self_instance=Some` branch, since outer model validators only run
    during the resumed pass for `custom_init` models; a non-`custom_init` model's outer validators
    run with `self_instance=None` throughout, so a `handler` call here never touches `self_instance`
    at all), so it is intentionally kept as a separate test.
    """
    calls = []

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        a: int

    built_once = {'v': False}

    def wrap_validator(value, handler, info):
        calls.append(('wrap-before', type(value).__name__))
        if isinstance(value, dict) and not built_once['v']:
            built_once['v'] = True
            # a different, already-existing instance that needs revalidation (not the raw `value`
            # this validator itself was called with)
            other = Model.__new__(Model)
            object.__setattr__(other, '__dict__', {'a': 999})
            object.__setattr__(other, '__pydantic_fields_set__', {'a'})
            object.__setattr__(other, '__pydantic_extra__', None)
            object.__setattr__(other, '__pydantic_private__', None)
            result = handler(other)
        else:
            result = handler(value)
        calls.append(('wrap-after', result.a))
        return result

    Model.__pydantic_validator__ = SchemaValidator(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema({'a': core_schema.model_field(core_schema.int_schema())}),
            config=CoreConfig(revalidate_instances='always'),
            model_validators=[{'type': 'wrap', 'function': {'type': 'with-info', 'function': wrap_validator}}],
        )
    )

    m = Model.__pydantic_validator__.validate_python({'a': 1})
    assert m.a == 999
    assert calls == [('wrap-before', 'dict'), ('wrap-after', 999)]


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


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
@pytest.mark.parametrize('validator', [None, 'field', 'model'])
def test_leak_model(validator):
    def fn():
        class Model:
            a: int

            @classmethod
            def _validator(cls, v, info):
                return v

            @classmethod
            def _wrap_validator(cls, v, validator, info):
                return validator(v)

        field_schema = core_schema.int_schema()
        if validator == 'field':
            field_schema = core_schema.with_info_before_validator_function(Model._validator, field_schema)
            field_schema = core_schema.with_info_wrap_validator_function(Model._wrap_validator, field_schema)
            field_schema = core_schema.with_info_after_validator_function(Model._validator, field_schema)

        model_schema = core_schema.model_schema(
            Model, core_schema.model_fields_schema({'a': core_schema.model_field(field_schema)})
        )

        if validator == 'model':
            model_schema = core_schema.with_info_before_validator_function(Model._validator, model_schema)
            model_schema = core_schema.with_info_wrap_validator_function(Model._wrap_validator, model_schema)
            model_schema = core_schema.with_info_after_validator_function(Model._validator, model_schema)

        # If any of the Rust validators don't implement traversal properly,
        # there will be an undetectable cycle created by this assignment
        # which will keep Model alive
        Model.__pydantic_validator__ = SchemaValidator(model_schema)

        return Model

    klass = fn()
    ref = weakref.ref(klass)
    assert ref() is not None

    del klass

    assert_gc(lambda: ref() is None)


def test_model_custom_init_with_union() -> None:
    class A:
        def __init__(self, **kwargs):
            assert 'a' in kwargs
            self.a = kwargs.get('a')

    class B:
        def __init__(self, **kwargs):
            assert 'b' in kwargs
            self.b = kwargs.get('b')

    schema = {
        'type': 'union',
        'choices': [
            {
                'type': 'model',
                'cls': A,
                'schema': {
                    'type': 'model-fields',
                    'fields': {'a': {'type': 'model-field', 'schema': {'type': 'bool'}}},
                    'model_name': 'A',
                },
                'custom_init': True,
                'ref': '__main__.A:4947206928',
            },
            {
                'type': 'model',
                'cls': B,
                'schema': {
                    'type': 'model-fields',
                    'fields': {'b': {'type': 'model-field', 'schema': {'type': 'bool'}}},
                    'model_name': 'B',
                },
                'custom_init': True,
                'ref': '__main__.B:4679932848',
            },
        ],
    }

    validator = SchemaValidator(schema)

    assert validator.validate_python({'a': False}).a is False
    assert validator.validate_python({'b': True}).b is True
