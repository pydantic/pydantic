"""Compatibility coverage for buffered compact JSON serialization of model unions."""

import json
import warnings
from collections import OrderedDict
from typing import Annotated, Any, Literal

import pytest
from pydantic_core import SchemaSerializer, core_schema

from pydantic import BaseModel, Field, TypeAdapter, field_serializer, model_serializer


def capture_json(serialize, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            output = serialize(**kwargs)
        except Exception as exc:
            result = (type(exc), str(exc))
        else:
            # Retain duplicate keys and their order, and compare NaN by representation.
            result = repr(json.loads(output, object_pairs_hook=lambda pairs: ('object', pairs)))
    return result, [str(w.message) for w in caught]


@pytest.mark.parametrize('tagged', [False, True])
@pytest.mark.parametrize(
    'payload',
    [
        [1.0, -0.0, float('inf'), float('nan')],
        {'text': ['привіт', '\U0001f600', '"\\\n'], 'nested': {'a': 1}},
        {1: 'first', '1': 'last', None: 'none', 'None': 'string'},
        [{1: 'first', '1': 'last'}],
        OrderedDict([(1, 'first'), ('1', 'last')]),
        (b'hello', {1, 2}, bytearray(b'world')),
        object(),
    ],
)
@pytest.mark.parametrize(
    'options',
    [
        {},
        {'ensure_ascii': True},
        {'round_trip': True},
        {'include': {'payload'}},
        {'exclude': {'payload': {0}}},
        {'fallback': str},
    ],
)
def test_model_union_compact_matches_pretty(tagged, payload, options):
    class A(BaseModel):
        payload: Any
        kind: Literal['a']

    class B(BaseModel):
        payload: Any
        kind: Literal['b']

    annotation = Annotated[A | B, Field(discriminator='kind')] if tagged else A | B
    adapter = TypeAdapter(annotation)
    value = A.model_construct(payload=payload, kind='a')

    assert capture_json(lambda **kw: adapter.dump_json(value, **kw), **options) == capture_json(
        lambda **kw: adapter.dump_json(value, indent=0, **kw), **options
    )


@pytest.mark.parametrize('tagged', [False, True])
@pytest.mark.parametrize('fields', [{'kind': 'a', 'tail': 'wrong'}, {'kind': 'a'}, {'kind': 'wrong', 'tail': 1}])
@pytest.mark.parametrize('warnings_mode', ['warn', 'error', 'none'])
def test_model_union_compact_failure_matches_pretty(tagged, fields, warnings_mode):
    class A(BaseModel):
        payload: Any
        kind: Literal['a']
        tail: int

    class B(BaseModel):
        payload: Any
        kind: Literal['b']
        tail: int

    annotation = Annotated[A | B, Field(discriminator='kind')] if tagged else A | B
    adapter = TypeAdapter(annotation)
    value = A.model_construct(payload=[1.0] * 10, **fields)

    assert capture_json(lambda **kw: adapter.dump_json(value, **kw), warnings=warnings_mode) == capture_json(
        lambda **kw: adapter.dump_json(value, indent=0, **kw), warnings=warnings_mode
    )


def test_model_union_discards_partially_serialized_candidate():
    class Model:
        def __init__(self):
            self.payload = [1.0] * 10
            self.tail = 1

    def schema(tail_schema):
        return core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'payload': core_schema.model_field(core_schema.any_schema()),
                    'tail': core_schema.model_field(tail_schema),
                }
            ),
        )

    # Both branches accept the runtime class, but float must reject int during
    # strict selection, after serializing the earlier payload field.
    serializer = SchemaSerializer(
        core_schema.union_schema([schema(core_schema.float_schema()), schema(core_schema.int_schema())])
    )
    expected = b'{"payload":[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],"tail":1}'
    assert serializer.to_json(Model()) == expected


@pytest.mark.parametrize('tagged', [False, True])
@pytest.mark.parametrize('model_wrapper', [False, True])
def test_model_union_custom_serializer_calls_match_pretty(tagged, model_wrapper):
    calls = []

    class A(BaseModel):
        payload: list[float]
        kind: Literal['a']

        @field_serializer('payload', mode='wrap')
        def serialize_payload(self, value, handler, info):
            calls.append(('field', info.field_name, info.mode, info.context))
            result = handler(value)
            assert isinstance(result, list)
            return result

        if model_wrapper:

            @model_serializer(mode='wrap')
            def serialize_model(self, handler, info):
                calls.append(('model', info.mode, info.context))
                result = handler(self)
                assert isinstance(result, dict)
                return result

    class B(BaseModel):
        payload: list[float]
        kind: Literal['b']

    annotation = Annotated[A | B, Field(discriminator='kind')] if tagged else A | B
    adapter = TypeAdapter(annotation)
    value = A(payload=[1.0], kind='a')
    expected = capture_json(lambda: adapter.dump_json(value, indent=0, context={'test': 1}))
    expected_calls = calls.copy()
    calls.clear()
    assert capture_json(lambda: adapter.dump_json(value, context={'test': 1})) == expected
    assert calls == expected_calls


def test_model_union_does_not_format_rejected_candidates():
    class A(BaseModel):
        text: str

    class B(BaseModel):
        number: int

    class Data(BaseModel):
        payload: Any

        def __repr__(self):
            pytest.fail('Successful union selection must not format rejected candidate errors')

    adapter = TypeAdapter(A | B | Data)
    assert adapter.dump_json(Data(payload=[1.0])) == b'{"payload":[1.0]}'


@pytest.mark.parametrize('failure', ['wrong_type', 'missing_field'])
def test_model_union_keeps_late_errors_lazy(failure):
    class Payload(list):
        def __repr__(self):
            pytest.fail('A discarded branch must not format its invalid field')

    class Model:
        def __init__(self):
            self.payload = Payload([1.0])

        def __repr__(self):
            pytest.fail('A discarded branch must not format its incomplete model')

    valid_fields = {'payload': core_schema.model_field(core_schema.any_schema())}
    invalid_fields = (
        {'payload': core_schema.model_field(core_schema.int_schema())}
        if failure == 'wrong_type'
        else {**valid_fields, 'missing': core_schema.model_field(core_schema.int_schema())}
    )
    serializer = SchemaSerializer(
        core_schema.union_schema(
            [
                core_schema.model_schema(Model, core_schema.model_fields_schema(invalid_fields)),
                core_schema.model_schema(Model, core_schema.model_fields_schema(valid_fields)),
            ]
        )
    )
    assert serializer.to_json(Model()) == b'{"payload":[1.0]}'


@pytest.mark.parametrize('tagged', [False, True])
@pytest.mark.parametrize('tail', [1, 'wrong'])
def test_nested_model_union_compact_matches_pretty(tagged, tail):
    class A(BaseModel):
        kind: Literal['a']
        tail: int

    class B(BaseModel):
        kind: Literal['b']
        tail: int

    class OuterA(BaseModel):
        kind: Literal['outer_a']
        inner: A | B

    class OuterB(BaseModel):
        kind: Literal['outer_b']
        inner: A | B

    annotation = Annotated[OuterA | OuterB, Field(discriminator='kind')] if tagged else OuterA | OuterB
    adapter = TypeAdapter(annotation)
    value = OuterA.model_construct(kind='outer_a', inner=A.model_construct(kind='a', tail=tail))
    assert capture_json(lambda: adapter.dump_json(value)) == capture_json(lambda: adapter.dump_json(value, indent=0))
