import pytest

from pydantic_core import SchemaSerializer


def test_branch_nullable():
    s = SchemaSerializer(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'sub_branch': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                },
            },
        }
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
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'sub_branch': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                },
            },
        }
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
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'sub_branch': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'nullable',
                        'schema': {
                            'type': 'definition-ref',
                            'schema_ref': 'Branch',
                            'serialization': {'type': 'to-string', 'when_used': 'always'},
                        },
                    },
                },
            },
        }
    )
    assert s.to_python({'name': 'root', 'sub_branch': {'name': 'branch', 'sub_branch': None}}) == {
        'name': 'root',
        'sub_branch': "{'name': 'branch', 'sub_branch': None}",
    }


def test_recursive_function():
    s = SchemaSerializer(
        {
            'type': 'typed-dict',
            'fields': {
                'root': {'type': 'typed-dict-field', 'schema': {'type': 'definition-ref', 'schema_ref': 'my_ref'}}
            },
            'ref': 'my_ref',
            'serialization': {'type': 'function-wrap', 'info_arg': True, 'function': lambda x, _1, _2: x},
        }
    )
    assert s.to_python({'root': {'root': {}}}) == {'root': {'root': {}}}


def test_recursive_function_deeper_ref():
    s = SchemaSerializer(
        {
            'type': 'typed-dict',
            'fields': {
                'a': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'typed-dict',
                        'ref': 'my_ref',
                        'fields': {
                            'b': {
                                'type': 'typed-dict-field',
                                'schema': {'type': 'definition-ref', 'schema_ref': 'my_ref'},
                            }
                        },
                    },
                }
            },
            'serialization': {
                'type': 'function-wrap',
                'is_field_serializer': False,
                'info_arg': True,
                'function': lambda x, _1, _2: x,
            },
        }
    )
    assert s.to_python({'a': {'b': {'b': {}}}}) == {'a': {'b': {'b': {}}}}
