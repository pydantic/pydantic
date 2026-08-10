"""What `SchemaValidator` / `SchemaSerializer` report to the garbage collector.

Their `tp_traverse` reports the Python objects held anywhere in the built validator / serializer structure (as many
times as they are held); these tests pin that down for representative schemas and check that reference cycles going
through validators and serializers stay collectable.
"""

import gc
import platform
import weakref
from collections import Counter
from typing import Any

import pytest
from pydantic_core import SchemaSerializer, SchemaValidator, core_schema


def _counts(obj: Any) -> Counter:
    return Counter(map(id, gc.get_referents(obj)))


class Model:
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'


def _model_schema(cls: type, default: Any, config: dict | None = None):
    return core_schema.model_schema(
        cls,
        core_schema.model_fields_schema(
            {
                'a': core_schema.model_field(core_schema.str_schema()),
                'b': core_schema.model_field(
                    core_schema.with_default_schema(core_schema.list_schema(core_schema.int_schema()), default=default)
                ),
                'c': core_schema.model_field(
                    core_schema.with_default_schema(core_schema.nullable_schema(core_schema.int_schema()), default=None)
                ),
            }
        ),
        config=config,
    )


@pytest.mark.skipif(platform.python_implementation() != 'CPython', reason='gc.get_referents() semantics')
def test_validator_referents_model():
    default = [1, 2]
    config = {'title': 'T', 'strict': False}
    schema = _model_schema(Model, default, config)
    v = SchemaValidator(schema, config)
    counts = _counts(v)
    assert counts[id(Model)] == 1
    assert counts[id(default)] == 1
    assert counts[id(None)] >= 1
    assert counts[id(schema)] == 1
    assert counts[id(config)] == 1
    # stable across calls (and across garbage collections)
    first = gc.get_referents(v)
    gc.collect()
    assert list(map(id, gc.get_referents(v))) == list(map(id, first))


@pytest.mark.skipif(platform.python_implementation() != 'CPython', reason='gc.get_referents() semantics')
def test_serializer_referents_model():
    default = [1, 2]
    schema = _model_schema(Model, default)
    s = SchemaSerializer(schema)
    counts = _counts(s)
    # the model serializer holds the class, and so does its root-model check
    assert counts[id(Model)] >= 1
    assert counts[id(default)] == 1
    assert counts[id(schema)] == 1


@pytest.mark.skipif(platform.python_implementation() != 'CPython', reason='gc.get_referents() semantics')
def test_referents_functions_and_definitions():
    def validate(v, info):
        return v

    def serialize(v):
        return v

    inner = core_schema.with_info_after_validator_function(
        validate,
        core_schema.int_schema(),
        serialization=core_schema.plain_serializer_function_ser_schema(serialize),
    )
    schema = core_schema.definitions_schema(
        core_schema.list_schema(core_schema.definition_reference_schema('d')),
        [
            core_schema.tuple_schema(
                [inner, core_schema.list_schema(core_schema.definition_reference_schema('d'))], ref='d'
            )
        ],
    )
    v = SchemaValidator(schema)
    s = SchemaSerializer(schema)
    v_counts = _counts(v)
    s_counts = _counts(s)
    # held once, inside the definition (definition references don't hold the definition's objects again)
    assert v_counts[id(validate)] == 1
    assert id(serialize) not in v_counts
    assert s_counts[id(serialize)] == 1
    assert id(validate) not in s_counts
    assert v.validate_python([(1, [])]) == [(1, [])]
    assert s.to_python([(1, [])]) == [(1, [])]


@pytest.mark.skipif(platform.python_implementation() != 'CPython', reason='gc.get_referents() semantics')
def test_prebuilt_referents_stop_at_the_reused_validator():
    class Inner(Model):
        pass

    class Outer(Model):
        pass

    inner_schema = core_schema.model_schema(
        Inner, core_schema.model_fields_schema({'x': core_schema.model_field(core_schema.int_schema())})
    )
    Inner.__pydantic_validator__ = SchemaValidator(inner_schema)
    Inner.__pydantic_serializer__ = SchemaSerializer(inner_schema)
    Inner.__pydantic_complete__ = True
    outer_schema = core_schema.model_schema(
        Outer, core_schema.model_fields_schema({'inner': core_schema.model_field(inner_schema)})
    )
    v = SchemaValidator(outer_schema)
    s = SchemaSerializer(outer_schema)
    v_counts = _counts(v)
    s_counts = _counts(s)
    assert v_counts[id(Inner.__pydantic_validator__)] == 1
    assert s_counts[id(Inner.__pydantic_serializer__)] == 1
    # the reused validator's own references are reported by it, not by the outer one
    assert id(Inner) not in v_counts
    assert v_counts[id(Outer)] == 1


def test_cycles_through_validator_and_serializer_are_collected():
    def make():
        class C(Model):
            pass

        def check(v, info):
            return v

        C.check = check
        schema = core_schema.model_schema(
            C,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.with_info_after_validator_function(check, core_schema.int_schema())
                    ),
                    'self': core_schema.model_field(
                        core_schema.with_default_schema(
                            core_schema.nullable_schema(core_schema.definition_reference_schema('C')), default=None
                        )
                    ),
                }
            ),
            ref='C',
        )
        schema = core_schema.definitions_schema(core_schema.definition_reference_schema('C'), [schema])
        C.__pydantic_validator__ = SchemaValidator(schema)
        C.__pydantic_serializer__ = SchemaSerializer(schema)
        # cycles: C -> validator -> (definitions -> model validator -> C, function -> C.check -> ... )
        instance = C.__pydantic_validator__.validate_python({'x': 1})
        assert instance.x == 1 and instance.self is None
        assert C.__pydantic_serializer__.to_python(instance) == {'x': 1, 'self': None}
        return weakref.ref(C)

    ref = make()
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    assert ref() is None


def test_referents_reported_while_collecting_during_construction():
    """A collection triggered while validators are being built (here: by allocating in a validator function used
    to compute a default) must not break anything."""

    calls = []

    def factory():
        calls.append(gc.collect())
        return 1

    schema = core_schema.typed_dict_schema(
        {
            'a': core_schema.typed_dict_field(
                core_schema.with_default_schema(
                    core_schema.int_schema(), default_factory=factory, validate_default=True
                )
            )
        }
    )
    v = SchemaValidator(schema)
    assert v.validate_python({}) == {'a': 1}
    assert calls
