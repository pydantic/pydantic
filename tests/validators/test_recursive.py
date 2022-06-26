from typing import Optional

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


def test_branch_nullable():
    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'Branch',
            'schema': {
                'type': 'model',
                'fields': {
                    'name': {'schema': {'type': 'str'}},
                    'sub_branch': {
                        'schema': {
                            'type': 'union',
                            'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'name': 'Branch'}],
                        },
                        'default': None,
                    },
                },
            },
        }
    )

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}

    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1'}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': None}}
    )
    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2'}}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2', 'sub_branch': None}}}
    )


def test_nullable_error():
    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'Branch',
            'schema': {
                'type': 'model',
                'fields': {
                    'width': {'schema': 'int'},
                    'sub_branch': {
                        'schema': {
                            'type': 'union',
                            'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'name': 'Branch'}],
                        },
                        'default': None,
                    },
                },
            },
        }
    )
    assert v.validate_python({'width': 123, 'sub_branch': {'width': 321}}) == (
        {'width': 123, 'sub_branch': {'width': 321, 'sub_branch': None}}
    )
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'width': 123, 'sub_branch': {'width': 'wrong'}})
    assert exc_info.value.errors() == [
        {
            'kind': 'none_required',
            'loc': ['sub_branch', 'none'],
            'message': 'Value must be None/null',
            'input_value': {'width': 'wrong'},
        },
        {
            'kind': 'int_parsing',
            'loc': ['sub_branch', 'recursive-ref', 'width'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        },
    ]


def test_list():
    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'BranchList',
            'schema': {
                'type': 'model',
                'fields': {
                    'width': {'schema': 'int'},
                    'branches': {
                        'schema': {'type': 'list', 'items': {'type': 'recursive-ref', 'name': 'BranchList'}},
                        'default': None,
                    },
                },
            },
        }
    )
    assert v.validate_python({'width': 1, 'branches': [{'width': 2}, {'width': 3, 'branches': [{'width': 4}]}]}) == (
        {
            'width': 1,
            'branches': [{'width': 2, 'branches': None}, {'width': 3, 'branches': [{'width': 4, 'branches': None}]}],
        }
    )


def test_multiple_intertwined():
    """
    like:
    from typing import List, Optional
    class Foo:
        height: int
        class Bar:
            width: int
            bars: List['Bar']
            foo: Optional['Foo']
        bar = Bar
    """

    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'Foo',
            'schema': {
                'type': 'model',
                'fields': {
                    'height': {'schema': 'int'},
                    'bar': {
                        'schema': {
                            'type': 'recursive-container',
                            'name': 'Bar',
                            'schema': {
                                'type': 'model',
                                'fields': {
                                    'width': {'schema': 'int'},
                                    'bars': {
                                        'schema': {'type': 'list', 'items': {'type': 'recursive-ref', 'name': 'Bar'}},
                                        'default': None,
                                    },
                                    'foo': {
                                        'schema': {
                                            'type': 'union',
                                            'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'name': 'Foo'}],
                                        },
                                        'default': None,
                                    },
                                },
                            },
                        }
                    },
                },
            },
        }
    )
    v.validate_python(
        {
            'height': 1,
            'bar': {
                'width': 2,
                'bars': [{'width': 3}],
                'foo': {'height': 4, 'bar': {'width': 5, 'bars': [], 'foo': None}},
            },
        }
    )


def test_model_class():
    class Branch:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        # these are here just as decoration
        width: int
        branch: Optional['Branch']  # noqa F821

    v = SchemaValidator(
        {
            'type': 'recursive-container',
            'name': 'Branch',
            'schema': {
                'type': 'model-class',
                'class_type': Branch,
                'model': {
                    'type': 'model',
                    'return_fields_set': True,
                    'fields': {
                        'width': {'schema': 'int'},
                        'branch': {
                            'schema': {
                                'type': 'union',
                                'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'name': 'Branch'}],
                            },
                            'default': None,
                        },
                    },
                },
            },
        }
    )
    m1: Branch = v.validate_python({'width': '1'})
    assert isinstance(m1, Branch)
    assert m1.__fields_set__ == {'width'}
    assert m1.__dict__ == {'width': 1, 'branch': None}
    assert m1.width == 1
    assert m1.branch is None

    m2: Branch = v.validate_python({'width': '10', 'branch': {'width': 20}})
    assert isinstance(m2, Branch)
    assert m2.__fields_set__ == {'width', 'branch'}
    assert m2.width == 10
    assert isinstance(m2.branch, Branch)
    assert m2.branch.width == 20
    assert m2.branch.branch is None


def test_invalid_schema():
    with pytest.raises(SchemaError, match="Recursive reference error: ref 'Branch' not found"):
        SchemaValidator(
            {
                'type': 'list',
                'items': {
                    'type': 'model',
                    'fields': {
                        'width': {'schema': {'type': 'int'}},
                        'branch': {
                            'schema': {'type': 'nullable', 'schema': {'type': 'recursive-ref', 'name': 'Branch'}},
                            'default': None,
                        },
                    },
                },
            }
        )
