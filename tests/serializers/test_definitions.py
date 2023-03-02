import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema

from ..conftest import plain_repr


def test_custom_ser():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
            [core_schema.int_schema(ref='foobar', serialization=core_schema.to_string_ser_schema(when_used='always'))],
        )
    )
    assert s.to_python([1, 2, 3]) == ['1', '2', '3']
    assert plain_repr(s).endswith('slots=[])')


def test_ignored_def():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.list_schema(core_schema.int_schema()),
            [core_schema.int_schema(ref='foobar', serialization=core_schema.to_string_ser_schema(when_used='always'))],
        )
    )
    assert s.to_python([1, 2, 3]) == [1, 2, 3]
    assert plain_repr(s).endswith('slots=[])')


def test_def_error():
    with pytest.raises(SchemaError) as exc_info:
        SchemaSerializer(
            core_schema.definitions_schema(
                core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
                [core_schema.int_schema(ref='foobar'), {'type': 'wrong'}],
            )
        )

    assert exc_info.value.args[0].startswith(
        "Invalid Schema:\ndefinitions -> definitions -> 1\n  Input tag 'wrong' found using self-schema"
    )


def test_repeated_ref():
    with pytest.raises(SchemaError, match='SchemaError: Duplicate ref: `foobar`'):
        SchemaSerializer(
            core_schema.tuple_positional_schema(
                core_schema.int_schema(ref='foobar'),
                core_schema.definition_reference_schema('foobar'),
                core_schema.int_schema(ref='foobar'),
            )
        )


def test_repeat_after():
    with pytest.raises(SchemaError, match='SchemaError: Duplicate ref: `foobar`'):
        SchemaSerializer(
            core_schema.tuple_positional_schema(
                core_schema.definitions_schema(
                    core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
                    [core_schema.int_schema(ref='foobar')],
                ),
                core_schema.int_schema(ref='foobar'),
            )
        )


def test_deep():
    v = SchemaSerializer(
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
                        [
                            core_schema.int_schema(
                                ref='foobar', serialization=core_schema.to_string_ser_schema(when_used='always')
                            )
                        ],
                    )
                ),
            }
        )
    )
    assert v.to_python({'a': 1, 'b': {'c': 2, 'd': 3}}) == {'a': 1, 'b': {'c': 2, 'd': '3'}}


def test_use_after():
    v = SchemaSerializer(
        core_schema.tuple_positional_schema(
            core_schema.definitions_schema(
                core_schema.definition_reference_schema('foobar'),
                [
                    core_schema.int_schema(
                        ref='foobar', serialization=core_schema.to_string_ser_schema(when_used='always')
                    )
                ],
            ),
            core_schema.definition_reference_schema('foobar'),
        )
    )
    assert v.to_python((1, 2)) == ('1', '2')
