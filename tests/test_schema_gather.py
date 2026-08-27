"""Tests for the core schema traversal used for schema cleaning (`pydantic._internal._schema_gather`)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic_core import core_schema as cs

from pydantic._internal._schema_gather import MissingDefinitionError, gather_schemas_for_cleaning


def disc(schema: Any) -> Any:
    schema['metadata'] = {'pydantic_internal_union_discriminator': 'kind'}
    return schema


def find_def_ref(schema: Any, ref: str) -> Any:
    """Find the (single) `'definition-ref'` schema object pointing to `ref`."""
    found: list[Any] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            if obj.get('type') == 'definition-ref' and obj['schema_ref'] == ref:
                found.append(obj)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)

    walk(schema)
    assert len(found) == 1
    return found[0]


def test_all_schema_kinds() -> None:
    int_schema = cs.int_schema()
    shared = cs.list_schema(cs.definition_reference_schema('shared'))
    definitions = {
        'a': cs.int_schema(ref='a'),
        'b': cs.str_schema(ref='b'),
        'shared': cs.float_schema(ref='shared'),
        'recursive': cs.list_schema(cs.definition_reference_schema('recursive'), ref='recursive'),
        'with_ser': cs.int_schema(ref='with_ser'),
        'fd': cs.int_schema(ref='fd'),
    }
    deferred_union_choice = disc(cs.str_schema())
    deferred_computed_field = disc(cs.str_schema())
    deferred_named_tuple_field = disc(cs.str_schema())
    schema = cs.definitions_schema(
        cs.typed_dict_schema(
            {
                'l': cs.typed_dict_field(cs.list_schema(cs.definition_reference_schema('a'))),
                't': cs.typed_dict_field(cs.tuple_schema([int_schema, cs.definition_reference_schema('b')])),
                'd': cs.typed_dict_field(cs.dict_schema(int_schema, cs.definition_reference_schema('b'))),
                'fd': cs.typed_dict_field(
                    {
                        'type': 'frozendict',
                        'keys_schema': int_schema,
                        'values_schema': cs.definition_reference_schema('fd'),
                    }
                ),
                'u': cs.typed_dict_field(cs.union_schema([(int_schema, 'x'), deferred_union_choice])),
                'tu': cs.typed_dict_field(cs.tagged_union_schema({'x': shared, 'y': shared}, 'kind')),
                'ch': cs.typed_dict_field(cs.chain_schema([int_schema, cs.str_schema()])),
                'ls': cs.typed_dict_field(cs.lax_or_strict_schema(cs.int_schema(), cs.str_schema())),
                'jp': cs.typed_dict_field(cs.json_or_python_schema(cs.int_schema(), cs.str_schema())),
                'rec': cs.typed_dict_field(cs.definition_reference_schema('recursive')),
                'mf': cs.typed_dict_field(
                    cs.model_fields_schema(
                        {'x': cs.model_field(cs.int_schema())},
                        computed_fields=[cs.computed_field('c', cs.int_schema())],
                        extras_schema=cs.str_schema(),
                    )
                ),
                'dc': cs.typed_dict_field(
                    cs.dataclass_args_schema(
                        'DC',
                        [cs.dataclass_field('x', cs.int_schema())],
                        computed_fields=[cs.computed_field('c', deferred_computed_field)],
                    )
                ),
                'nt': cs.typed_dict_field(
                    cs.named_tuple_schema(
                        tuple,
                        [
                            cs.named_tuple_field('x', cs.int_schema()),
                            cs.named_tuple_field('y', deferred_named_tuple_field),
                        ],
                    )
                ),
                'args': cs.typed_dict_field(
                    cs.arguments_schema(
                        [cs.arguments_parameter('x', cs.int_schema())],
                        var_args_schema=cs.int_schema(),
                        var_kwargs_schema=cs.str_schema(),
                    )
                ),
                'args3': cs.typed_dict_field(cs.arguments_v3_schema([cs.arguments_v3_parameter('x', cs.int_schema())])),
                'call': cs.typed_dict_field(
                    cs.call_schema(cs.arguments_schema([]), lambda: None, return_schema=cs.int_schema())
                ),
                'fb': cs.typed_dict_field(
                    cs.no_info_before_validator_function(
                        lambda v: v, cs.int_schema(), json_schema_input_schema=cs.str_schema()
                    )
                ),
                'fp': cs.typed_dict_field(
                    cs.no_info_plain_validator_function(lambda v: v, json_schema_input_schema=cs.str_schema())
                ),
                'fw': cs.typed_dict_field(
                    cs.no_info_wrap_validator_function(
                        lambda v, h: v, cs.int_schema(), json_schema_input_schema=cs.str_schema()
                    )
                ),
                'ser': cs.typed_dict_field(
                    cs.any_schema(
                        serialization=cs.plain_serializer_function_ser_schema(
                            lambda v: v, return_schema=cs.definition_reference_schema('with_ser')
                        )
                    )
                ),
                'nullable': cs.typed_dict_field(cs.nullable_schema(cs.definition_reference_schema('shared'))),
                'def_ref_ser': cs.typed_dict_field(
                    cs.definition_reference_schema(
                        'a', serialization=cs.plain_serializer_function_ser_schema(lambda v: v)
                    )
                ),
            }
        ),
        [cs.int_schema(ref='unused')],
    )

    result = gather_schemas_for_cleaning(schema, definitions)
    # in encounter order:
    assert list(result['collected_references']) == ['a', 'b', 'fd', 'shared', 'recursive', 'with_ser']
    assert result['collected_references'] == {
        'a': None,
        'b': None,
        'fd': find_def_ref(schema, 'fd'),
        'shared': None,
        'recursive': None,
        'with_ser': find_def_ref(schema, 'with_ser'),
    }
    assert result['collected_references']['with_ser'] is find_def_ref(schema, 'with_ser')
    assert [id(s) for s in result['deferred_discriminator_schemas']] == [
        id(deferred_union_choice),
        id(deferred_computed_field),
        id(deferred_named_tuple_field),
    ]


def test_inlinable_reference_identity() -> None:
    def_ref = cs.definition_reference_schema('a')
    result = gather_schemas_for_cleaning(cs.list_schema(def_ref), {'a': cs.int_schema(ref='a')})
    assert result['collected_references'] == {'a': def_ref}
    assert result['collected_references']['a'] is def_ref
    assert result['deferred_discriminator_schemas'] == []


def test_shared_schema_objects_are_not_inlined() -> None:
    # the same schema object reachable twice: references inside can't be inlined
    inner = cs.list_schema(cs.definition_reference_schema('a'))
    result = gather_schemas_for_cleaning(cs.tuple_schema([inner, inner]), {'a': cs.int_schema(ref='a')})
    assert result['collected_references'] == {'a': None}


def test_definition_ref_reachable_from_its_definition() -> None:
    # the 'definition-ref' schema object is reachable from the definition it points to
    # (it is encountered again while being traversed), so it can't be inlined:
    def_ref = cs.definition_reference_schema('a')
    definitions: dict[str, Any] = {'a': cs.list_schema(def_ref, ref='a')}
    result = gather_schemas_for_cleaning(cs.tuple_schema([def_ref]), definitions)
    assert result['collected_references'] == {'a': None}


def test_definition_ref_serialization_and_metadata() -> None:
    # the serialization schema and metadata of a 'definition-ref' schema are only considered
    # the first time it is encountered:
    def_ref = disc(
        cs.definition_reference_schema(
            'a', serialization=cs.plain_serializer_function_ser_schema(lambda v: v, return_schema=disc(cs.int_schema()))
        )
    )
    definitions: dict[str, Any] = {'a': cs.int_schema(ref='a')}
    result = gather_schemas_for_cleaning(cs.tuple_schema([def_ref]), definitions)
    assert result['collected_references'] == {'a': def_ref}
    assert [id(s) for s in result['deferred_discriminator_schemas']] == [
        id(def_ref['serialization']['return_schema']),
        id(def_ref),
    ]

    result = gather_schemas_for_cleaning(cs.tuple_schema([def_ref, def_ref]), definitions)
    assert result['collected_references'] == {'a': None}
    assert len(result['deferred_discriminator_schemas']) == 2


@pytest.mark.parametrize(
    ['schema', 'definitions'],
    [
        (cs.definition_reference_schema('missing'), {}),
        (cs.list_schema(cs.definition_reference_schema('missing')), {'other': cs.int_schema()}),
    ],
)
def test_missing_definition(schema: Any, definitions: dict[str, Any]) -> None:
    with pytest.raises(MissingDefinitionError) as exc_info:
        gather_schemas_for_cleaning(schema, definitions)
    assert isinstance(exc_info.value, LookupError)
    assert exc_info.value.schema_reference == 'missing'


@pytest.mark.parametrize(
    ['schema', 'exc_type'],
    [
        ([], TypeError),
        ({'no_type': True}, KeyError),
        ({'type': 123}, TypeError),
        ({'type': 'model-fields'}, KeyError),
        ({'type': 'model-fields', 'fields': 1}, AttributeError),
        ({'type': 'lax-or-strict', 'lax_schema': cs.int_schema()}, KeyError),
        ({'type': 'definition-ref'}, KeyError),
    ],
)
def test_unexpected_structures(schema: Any, exc_type: type[Exception]) -> None:
    with pytest.raises(exc_type):
        gather_schemas_for_cleaning(schema, {})


def test_iterables() -> None:
    # any iterable is accepted where the schema types are defined with lists:
    def_ref = cs.definition_reference_schema('a')
    schema: Any = {
        'type': 'definitions',
        'schema': {'type': 'tuple', 'items_schema': (def_ref,)},
        'definitions': iter([cs.int_schema(ref='unused')]),
    }
    result = gather_schemas_for_cleaning(schema, {'a': cs.int_schema(ref='a')})
    assert result['collected_references'] == {'a': def_ref}


def test_deeply_nested_schema() -> None:
    schema: Any = cs.definition_reference_schema('a')
    for _ in range(10_000):
        schema = cs.list_schema(schema)
    result = gather_schemas_for_cleaning(schema, {'a': cs.int_schema(ref='a')})
    assert list(result['collected_references']) == ['a']
