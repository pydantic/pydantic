import pytest

from pydantic_core import SchemaError, SchemaValidator, core_schema, validate_core_schema

from ..conftest import plain_repr


def test_list_with_def():
    v = SchemaValidator(
        core_schema.definitions_schema(
            core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
            [core_schema.int_schema(ref='foobar')],
        )
    )
    assert v.validate_python([1, 2, '3']) == [1, 2, 3]
    assert v.validate_json(b'[1, 2, "3"]') == [1, 2, 3]
    r = plain_repr(v)
    assert r.startswith('SchemaValidator(title="list[int]",')


def test_ignored_def():
    v = SchemaValidator(
        core_schema.definitions_schema(
            core_schema.list_schema(core_schema.int_schema()), [core_schema.int_schema(ref='foobar')]
        )
    )
    assert v.validate_python([1, 2, '3']) == [1, 2, 3]
    r = plain_repr(v)
    assert r.startswith('SchemaValidator(title="list[int]",')


def test_extract_used_refs_ignores_metadata():
    v = SchemaValidator(core_schema.any_schema(metadata={'type': 'definition-ref'}))
    assert v.validate_python([1, 2, 3]) == [1, 2, 3]
    assert plain_repr(v).endswith('definitions=[])')


def test_check_ref_used_ignores_metadata():
    v = SchemaValidator(
        core_schema.list_schema(
            core_schema.int_schema(metadata={'type': 'definition-ref', 'schema_ref': 'foobar'}), ref='foobar'
        )
    )
    assert v.validate_python([1, 2, 3]) == [1, 2, 3]
    # assert plain_repr(v).endswith('definitions=[])')


def test_def_error():
    with pytest.raises(SchemaError) as exc_info:
        validate_core_schema(
            core_schema.definitions_schema(
                core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
                [core_schema.int_schema(ref='foobar'), {'type': 'wrong'}],
            )
        )
    assert str(exc_info.value).startswith(
        "Invalid Schema:\ndefinitions.definitions.1\n  Input tag 'wrong' found using 'type'"
    )
    assert exc_info.value.error_count() == 1


def test_dict_repeat():
    v = SchemaValidator(
        core_schema.definitions_schema(
            core_schema.dict_schema(
                core_schema.definition_reference_schema('foobar'), core_schema.definition_reference_schema('foobar')
            ),
            [core_schema.int_schema(ref='foobar')],
        )
    )
    assert v.validate_python({'1': '2', 3: '4'}) == {1: 2, 3: 4}
    assert v.validate_json(b'{"1": 2, "3": "4"}') == {1: 2, 3: 4}
    # assert plain_repr(v).endswith('definitions=[])')


def test_repeated_ref():
    with pytest.raises(SchemaError, match='SchemaError: Duplicate ref: `foobar`'):
        SchemaValidator(
            core_schema.tuple_positional_schema(
                [
                    core_schema.definitions_schema(
                        core_schema.definition_reference_schema('foobar'), [core_schema.int_schema(ref='foobar')]
                    ),
                    core_schema.definitions_schema(
                        core_schema.definition_reference_schema('foobar'), [core_schema.int_schema(ref='foobar')]
                    ),
                ]
            )
        )


def test_repeat_after():
    with pytest.raises(SchemaError, match='SchemaError: Duplicate ref: `foobar`'):
        SchemaValidator(
            core_schema.definitions_schema(
                core_schema.tuple_positional_schema(
                    [
                        core_schema.definitions_schema(
                            core_schema.definition_reference_schema('foobar'), [core_schema.int_schema(ref='foobar')]
                        ),
                        core_schema.definition_reference_schema('foobar'),
                    ]
                ),
                [core_schema.int_schema(ref='foobar')],
            )
        )


def test_deep():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema()),
                'b': core_schema.typed_dict_field(
                    core_schema.definitions_schema(
                        core_schema.typed_dict_schema(
                            {
                                'c': core_schema.typed_dict_field(core_schema.int_schema()),
                                'd': core_schema.typed_dict_field(core_schema.definition_reference_schema('foobar')),
                            }
                        ),
                        [core_schema.str_schema(ref='foobar')],
                    )
                ),
            }
        )
    )
    assert v.validate_python({'a': 1, 'b': {'c': 2, 'd': b'dd'}}) == {'a': 1, 'b': {'c': 2, 'd': 'dd'}}


def test_use_after():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [
                core_schema.definitions_schema(
                    core_schema.definition_reference_schema('foobar'), [core_schema.int_schema(ref='foobar')]
                ),
                core_schema.definition_reference_schema('foobar'),
            ]
        )
    )
    assert v.validate_python(['1', '2']) == (1, 2)
