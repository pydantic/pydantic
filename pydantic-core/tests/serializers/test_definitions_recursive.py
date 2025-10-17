import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_branch_nullable():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.definition_reference_schema('Branch'),
            [
                core_schema.typed_dict_schema(
                    {
                        'name': core_schema.typed_dict_field(core_schema.str_schema()),
                        'sub_branch': core_schema.typed_dict_field(
                            core_schema.nullable_schema(core_schema.definition_reference_schema('Branch'))
                        ),
                    },
                    ref='Branch',
                )
            ],
        )
    )
    assert s.to_python({'name': 'root', 'sub_branch': {'name': 'branch', 'sub_branch': None}}) == {
        'name': 'root',
        'sub_branch': {'name': 'branch', 'sub_branch': None},
    }
    assert s.to_python({'name': 'root', 'sub_branch': {'name': 'branch', 'sub_branch': None}}, exclude_none=True) == {
        'name': 'root',
        'sub_branch': {'name': 'branch'},
    }


def test_cyclic_recursion():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.definition_reference_schema('Branch'),
            [
                core_schema.typed_dict_schema(
                    {
                        'name': core_schema.typed_dict_field(core_schema.str_schema()),
                        'sub_branch': core_schema.typed_dict_field(
                            core_schema.nullable_schema(core_schema.definition_reference_schema('Branch'))
                        ),
                    },
                    ref='Branch',
                )
            ],
        )
    )
    v = {'name': 'root'}
    v['sub_branch'] = v
    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        s.to_python(v)
    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        s.to_python(v, mode='json')
    with pytest.raises(ValueError, match=r'Circular reference detected \(id repeated\)'):
        s.to_json(v)


def test_custom_ser():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.definition_reference_schema('Branch'),
            [
                core_schema.typed_dict_schema(
                    {
                        'name': core_schema.typed_dict_field(core_schema.str_schema()),
                        'sub_branch': core_schema.typed_dict_field(
                            core_schema.nullable_schema(
                                core_schema.definition_reference_schema(
                                    'Branch', serialization=core_schema.to_string_ser_schema(when_used='always')
                                )
                            )
                        ),
                    },
                    ref='Branch',
                )
            ],
        )
    )
    assert s.to_python({'name': 'root', 'sub_branch': {'name': 'branch', 'sub_branch': None}}) == {
        'name': 'root',
        'sub_branch': "{'name': 'branch', 'sub_branch': None}",
    }


def test_recursive_function():
    s = SchemaSerializer(
        core_schema.definitions_schema(
            core_schema.definition_reference_schema('my_ref'),
            [
                core_schema.typed_dict_schema(
                    {'root': core_schema.typed_dict_field(core_schema.definition_reference_schema('my_ref'))},
                    ref='my_ref',
                    serialization=core_schema.wrap_serializer_function_ser_schema(function=lambda x, _handler: x),
                )
            ],
        )
    )
    assert s.to_python({'root': {'root': {}}}) == {'root': {'root': {}}}


def test_recursive_function_deeper_ref():
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(
                    core_schema.definitions_schema(
                        core_schema.definition_reference_schema('my_ref'),
                        [
                            core_schema.typed_dict_schema(
                                {'b': core_schema.typed_dict_field(core_schema.definition_reference_schema('my_ref'))},
                                ref='my_ref',
                            )
                        ],
                    )
                )
            },
            serialization=core_schema.wrap_serializer_function_ser_schema(
                function=lambda x, _handler: x, is_field_serializer=False
            ),
        )
    )
    assert s.to_python({'a': {'b': {'b': {}}}}) == {'a': {'b': {'b': {}}}}
