import platform
import sys
from collections.abc import Iterable
from typing import Any
from weakref import WeakValueDictionary

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from .conftest import assert_gc, is_free_threaded

GC_TEST_SCHEMA_INNER = core_schema.definitions_schema(
    core_schema.definition_reference_schema(schema_ref='model'),
    [
        core_schema.typed_dict_schema(
            {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema(schema_ref='model'))},
            ref='model',
        )
    ],
)


@pytest.mark.xfail(is_free_threaded and sys.version_info < (3, 14), reason='GC leaks on free-threaded (<3.14)')
@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_schema_serializer() -> None:
    # test for https://github.com/pydantic/pydantic/issues/5136
    class BaseModel:
        __schema__: SchemaSerializer

        def __init_subclass__(cls) -> None:
            cls.__schema__ = SchemaSerializer(
                core_schema.model_schema(cls, GC_TEST_SCHEMA_INNER), config={'ser_json_timedelta': 'float'}
            )

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyModel(BaseModel):
            pass

        cache[id(MyModel)] = MyModel

        del MyModel

    assert_gc(lambda: len(cache) == 0)


@pytest.mark.xfail(is_free_threaded and sys.version_info < (3, 14), reason='GC leaks on free-threaded (<3.14)')
@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
def test_gc_schema_validator() -> None:
    # test for https://github.com/pydantic/pydantic/issues/5136
    class BaseModel:
        __validator__: SchemaValidator

        def __init_subclass__(cls) -> None:
            cls.__validator__ = SchemaValidator(
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


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
@pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy')
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
