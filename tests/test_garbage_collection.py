import gc
import platform
from typing import Any, Iterable
from weakref import WeakValueDictionary

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

GC_TEST_SCHEMA_INNER = core_schema.definitions_schema(
    core_schema.definition_reference_schema(schema_ref='model'),
    [
        core_schema.typed_dict_schema(
            {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema(schema_ref='model'))},
            ref='model',
        )
    ],
)


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_gc_schema_serializer() -> None:
    # test for https://github.com/pydantic/pydantic/issues/5136
    class BaseModel:
        __schema__: SchemaSerializer

        def __init_subclass__(cls) -> None:
            cls.__schema__ = SchemaSerializer(
                core_schema.model_schema(cls, GC_TEST_SCHEMA_INNER), config={'ser_json_timedelta': 'seconds_float'}
            )

    cache: 'WeakValueDictionary[int, Any]' = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)

    assert len(cache) == 0


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_gc_schema_validator() -> None:
    # test for https://github.com/pydantic/pydantic/issues/5136
    class BaseModel:
        __validator__: SchemaValidator

        def __init_subclass__(cls) -> None:
            cls.__validator__ = SchemaValidator(
                core_schema.model_schema(cls, GC_TEST_SCHEMA_INNER),
                config=core_schema.CoreConfig(extra_fields_behavior='allow'),
            )

    cache: 'WeakValueDictionary[int, Any]' = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)

    assert len(cache) == 0


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_gc_validator_iterator() -> None:
    # test for https://github.com/pydantic/pydantic/issues/9243
    class MyModel:
        iter: Iterable[int]

    v = SchemaValidator(
        core_schema.model_schema(
            MyModel,
            core_schema.model_fields_schema(
                {'iter': core_schema.model_field(core_schema.generator_schema(core_schema.int_schema()))}
            ),
        ),
    )

    class MyIterable:
        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration()

    cache: 'WeakValueDictionary[int, Any]' = WeakValueDictionary()

    for _ in range(10_000):
        iterable = MyIterable()
        cache[id(iterable)] = iterable
        v.validate_python({'iter': iterable})
        del iterable

    gc.collect(0)
    gc.collect(1)
    gc.collect(2)

    assert len(cache) == 0
