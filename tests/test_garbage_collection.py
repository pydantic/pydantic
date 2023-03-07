import gc
import platform
from typing import Any
from weakref import WeakValueDictionary

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_gc_schema_serializer() -> None:
    # test for https://github.com/pydantic/pydantic/issues/5136
    class BaseModel:
        __schema__: SchemaSerializer

        def __init_subclass__(cls) -> None:
            cls.__schema__ = SchemaSerializer(
                core_schema.model_schema(
                    cls,
                    core_schema.typed_dict_schema(
                        {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema('model'))}
                    ),
                    ref='model',
                )
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
                core_schema.model_schema(
                    cls,
                    core_schema.typed_dict_schema(
                        {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema('model'))}
                    ),
                    ref='model',
                )
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
