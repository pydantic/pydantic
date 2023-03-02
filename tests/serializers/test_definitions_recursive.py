import pytest

from pydantic_core import SchemaSerializer


def test_branch_nullable():
    s = SchemaSerializer(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'schema': {'type': 'str'}},
                'sub_branch': {
                    'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}}
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
                'name': {'schema': {'type': 'str'}},
                'sub_branch': {
                    'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}}
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
                'name': {'schema': {'type': 'str'}},
                'sub_branch': {
                    'schema': {
                        'type': 'nullable',
                        'schema': {
                            'type': 'definition-ref',
                            'schema_ref': 'Branch',
                            'serialization': {'type': 'to-string', 'when_used': 'always'},
                        },
                    }
                },
            },
        }
    )
    assert s.to_python({'name': 'root', 'sub_branch': {'name': 'branch', 'sub_branch': None}}) == {
        'name': 'root',
        'sub_branch': "{'name': 'branch', 'sub_branch': None}",
    }
