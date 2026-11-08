import gc
import platform
import weakref
from collections.abc import Iterable
from enum import StrEnum
from typing import Any
from weakref import WeakValueDictionary

import pytest

from pydantic_core import (
    ArgsKwargs,
    PydanticCustomError,
    PydanticKnownError,
    SchemaSerializer,
    SchemaValidator,
    ValidationError,
    core_schema,
)

from .conftest import assert_gc

pytestmark = [
    pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='https://github.com/pypy/pypy/issues/3898'),
    pytest.mark.skipif(platform.python_implementation() == 'GraalVM', reason='Cannot reliably trigger GC on GraalPy'),
]

GC_TEST_SCHEMA_INNER = core_schema.definitions_schema(
    core_schema.definition_reference_schema(schema_ref='model'),
    [
        core_schema.typed_dict_schema(
            {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema(schema_ref='model'))},
            ref='model',
        )
    ],
)


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


def test_gc_enum_serializer_class() -> None:
    """https://github.com/pydantic/pydantic/issues/13621"""

    class EnumBase:
        __pydantic_serializer__: SchemaSerializer

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyEnum(EnumBase, StrEnum):
            FULL = 'full'

        MyEnum.__pydantic_serializer__ = SchemaSerializer(core_schema.enum_schema(MyEnum, list(MyEnum), sub_type='str'))

        cache[id(MyEnum)] = MyEnum

        del MyEnum

    assert_gc(lambda: len(cache) == 0)


def test_gc_enum_validator_lookup() -> None:
    """https://github.com/pydantic/pydantic/issues/13621"""

    class EnumBase:
        __pydantic_validator__: SchemaValidator

    cache: WeakValueDictionary[int, Any] = WeakValueDictionary()

    for _ in range(10_000):

        class MyEnum(EnumBase, StrEnum):
            FULL = 'full'

        MyEnum.__pydantic_validator__ = SchemaValidator(core_schema.enum_schema(MyEnum, list(MyEnum), sub_type='str'))

        cache[id(MyEnum)] = MyEnum

        del MyEnum

    assert_gc(lambda: len(cache) == 0)


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


@pytest.mark.skipif(
    platform.python_implementation() == 'GraalVM', reason='GC introspection is not supported on GraalPy'
)
def test_wrap_validator_handler_does_not_traverse_shared_validator_tree() -> None:
    """https://github.com/pydantic/pydantic/issues/13817"""

    class Model:
        __slots__ = '__dict__', '__pydantic_extra__', '__pydantic_fields_set__', '__pydantic_private__'

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


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy',
    reason='https://github.com/pypy/pypy/issues/3898 + gc.is_tracked() unavailable',
)
@pytest.mark.skipif(
    platform.python_implementation() == 'GraalVM', reason='GC introspection is not supported on GraalPy'
)
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


def test_validation_error_traverses_inner_exception() -> None:
    """https://github.com/pydantic/pydantic/issues/14237"""

    class Marker:
        pass

    def validate(value):
        raise ValueError(Marker())

    v = SchemaValidator(core_schema.no_info_plain_validator_function(validate))
    markers = []

    def attempt():
        try:
            v.validate_python(1)
        except ValidationError as error:
            markers.append(weakref.ref(error.errors()[0]['ctx']['error'].args[0]))
            # cycle: frame -> error -> inner `ValueError` -> traceback -> frame
            saved = error
            assert saved is error

    for _ in range(10):
        attempt()

    gc.collect()
    assert all(marker() is None for marker in markers)


def _gc_reaches(obj: Any, target: Any, depth: int = 3) -> bool:
    """Whether `target` is reachable from `obj` through `tp_traverse` edges only."""
    if depth == 0:
        return False
    referents = gc.get_referents(obj)
    return any(r is target for r in referents) or any(_gc_reaches(r, target, depth - 1) for r in referents)


@pytest.mark.xfail(
    reason="'ArgsKwargs' uses a freelist, and GC is broken on reused objects from the freelist (https://github.com/PyO3/pyo3/pull/6442)"
)
def test_exceptions_and_markers_report_python_references() -> None:
    """https://github.com/pydantic/pydantic/issues/14237"""
    marker = object()

    custom_error = PydanticCustomError('my_error', 'message', {'value': marker})
    assert gc.is_tracked(custom_error)
    assert _gc_reaches(custom_error, marker)

    known_error = PydanticKnownError('value_error', {'error': marker})
    assert gc.is_tracked(known_error)
    assert _gc_reaches(known_error, marker)

    args_kwargs = ArgsKwargs((marker,), {'kw': marker})
    assert gc.is_tracked(args_kwargs)
    assert _gc_reaches(args_kwargs, marker)
