import gc
import platform
from collections.abc import Iterable
from enum import Enum
from typing import Any
from weakref import WeakValueDictionary

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from .conftest import assert_gc

GC_TEST_SCHEMA_INNER = core_schema.definitions_schema(
    core_schema.definition_reference_schema(schema_ref='model'),
    [
        core_schema.typed_dict_schema(
            {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema(schema_ref='model'))},
            ref='model',
        )
    ],
)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_schema_serializer() -> None:
    """https://github.com/pydantic/pydantic/issues/5136"""

    class BaseModel:
        __pydantic_core_schema__: SchemaSerializer

        def __init_subclass__(cls) -> None:
            cls.__pydantic_core_schema__ = SchemaSerializer(
                core_schema.model_schema(cls, GC_TEST_SCHEMA_INNER), config={'ser_json_timedelta': 'float'}
            )

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_schema_validator() -> None:
    """https://github.com/pydantic/pydantic/issues/5136"""

    class BaseModel:
        __pydantic_validator__: SchemaValidator

        def __init_subclass__(cls) -> None:
            cls.__pydantic_validator__ = SchemaValidator(
                schema=core_schema.model_schema(cls, GC_TEST_SCHEMA_INNER),
                config=core_schema.CoreConfig(extra_fields_behavior='allow'),
            )

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_validator_iterator() -> None:
    """https://github.com/pydantic/pydantic/issues/9243"""

    class MyModel:
        iter: Iterable[int]

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {'iter': core_schema.model_field(core_schema.generator_schema(core_schema.int_schema()))}
            ),
        )
    )

    class MyIterable:
        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration()

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):
        iterable = MyIterable()
        cache[id(iterable)] = iterable
        v.validate_python({'iter': iterable})
        del iterable

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_enum_serializer_class() -> None:
    """https://github.com/pydantic/pydantic/issues/13621"""

    class EnumBase:
        __pydantic_serializer__: SchemaSerializer

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyEnum(EnumBase, str, Enum):
            FULL = 'full'

        MyEnum.__pydantic_serializer__ = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum), sub_type='str'))

        cache[id(MyEnum)] = MyEnum

        del MyEnum

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_enum_validator_lookup() -> None:
    """https://github.com/pydantic/pydantic/issues/13621"""

    class EnumBase:
        __pydantic_validator__: SchemaValidator

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyEnum(EnumBase, str, Enum):
            FULL = 'full'

        MyEnum.__pydantic_validator__ = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum), sub_type='str'))

        cache[id(MyEnum)] = MyEnum

        del MyEnum

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898')
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_field_exclude_if() -> None:
    """https://github.com/pydantic/pydantic/issues/13621"""

    class Dummy:
        pass

    class BaseModel:
        __pydantic_serializer__: SchemaSerializer

        def __init_subclass__(cls) -> None:
            cls.__pydantic_serializer__ = SchemaSerializer(
                core_schema.model_schema(
                    Dummy,
                    core_schema.model_fields_schema(
                        {
                            'value': core_schema.model_field(
                                core_schema.int_schema(), serialization_exclude_if=lambda value, _cls=cls: False
                            )
                        }
                    ),
                )
            )

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    assert_gc(lambda: len(cache) == 0)


def test_wrap_validator_handler_does_not_traverse_shared_validator_tree() -> None:
    """https://github.com/pydantic/pydantic/issues/13817"""

    class Model:
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    handlers = []

    def wrap(value, handler):
        handlers.append(handler)
        return handler(value)

    v = SchemaValidator(
        core_schema.no_info_wrap_validator_function(
            wrap,
            core_schema.model_schema(
                Model,
                core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.int_schema())}),
            ),
        )
    )
    v.validate_python({'x': 1})
    (handler,) = handlers

    # the `SchemaValidator` owns the validator tree and reports the model class to the GC:
    assert any(r is Model for r in gc.get_referents(v))
    # the handler shares that same tree, so it must not report it a second time:
    assert not any(r is Model for r in gc.get_referents(handler))


def test_wrap_serializer_handler_does_not_traverse_shared_serializer_tree() -> None:
    """https://github.com/pydantic/pydantic/issues/13817"""

    def field_serializer(value):
        return value

    inner = core_schema.typed_dict_schema(
        {
            'x': core_schema.typed_dict_field(
                core_schema.int_schema(serialization=core_schema.plain_serializer_function_ser_schema(field_serializer))
            )
        }
    )

    handlers = []

    def wrap(value, handler):
        handlers.append(handler)
        return handler(value)

    s = SchemaSerializer(
        core_schema.any_schema(serialization=core_schema.wrap_serializer_function_ser_schema(wrap, schema=inner))
    )
    s.to_python({'x': 1})
    (handler,) = handlers
    assert gc.is_tracked(handler)

    # the `SchemaSerializer` owns the serializer tree and reports the function to the GC:
    assert any(r is field_serializer for r in gc.get_referents(s))
    # the handler shares that same tree, so it must not report it a second time:
    assert not any(r is field_serializer for r in gc.get_referents(handler))

    s = SchemaSerializer(core_schema.generator_schema(inner))
    iterator = s.to_python(iter([{'x': 1}]))
    assert gc.is_tracked(iterator)
    assert not any(r is field_serializer for r in gc.get_referents(iterator))
