import platform
from dataclasses import dataclass
from typing import List, Optional

import pytest
from dirty_equals import AnyThing, HasAttributes, IsList, IsPartialDict, IsStr, IsTuple

import pydantic_core
from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, plain_repr
from .test_typed_dict import Cls


def test_branch_nullable():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'sub_branch': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                        'default': None,
                    },
                },
            },
        }
    )

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}
    assert plain_repr(v).startswith(
        'SchemaValidator(title="typed-dict",validator=DefinitionRef(DefinitionRefValidator{'
    )
    assert ',definitions=[TypedDict(TypedDictValidator{' in plain_repr(v)

    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1'}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': None}}
    )
    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2'}}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2', 'sub_branch': None}}}
    )


def test_branch_nullable_definitions():
    v = SchemaValidator(
        core_schema.definitions_schema(
            {'type': 'definition-ref', 'schema_ref': 'Branch'},
            [
                {
                    'type': 'typed-dict',
                    'ref': 'Branch',
                    'fields': {
                        'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                        'sub_branch': {
                            'type': 'typed-dict-field',
                            'schema': {
                                'type': 'default',
                                'schema': {
                                    'type': 'nullable',
                                    'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                },
                                'default': None,
                            },
                        },
                    },
                }
            ],
        )
    )

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}

    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1'}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': None}}
    )
    assert v.validate_python({'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2'}}}) == (
        {'name': 'root', 'sub_branch': {'name': 'b1', 'sub_branch': {'name': 'b2', 'sub_branch': None}}}
    )
    assert ',definitions=[TypedDict(TypedDictValidator{' in plain_repr(v)


def test_unused_ref():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'other': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            },
        }
    )
    assert v.validate_python({'name': 'root', 'other': '4'}) == {'name': 'root', 'other': 4}


def test_nullable_error():
    v = SchemaValidator(
        {
            'ref': 'Branch',
            'type': 'typed-dict',
            'fields': {
                'width': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                'sub_branch': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'default',
                        'schema': {
                            'type': 'union',
                            'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Branch'}],
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
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'none_required',
            'loc': ('sub_branch', 'none'),
            'msg': 'Input should be None',
            'input': {'width': 'wrong'},
        },
        {
            'type': 'int_parsing',
            'loc': ('sub_branch', 'typed-dict', 'width'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        },
    ]


def test_list():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'BranchList',
            'fields': {
                'width': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                'branches': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'default',
                        'schema': {
                            'type': 'list',
                            'items_schema': {'type': 'definition-ref', 'schema_ref': 'BranchList'},
                        },
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
    assert ',definitions=[TypedDict(TypedDictValidator{' in plain_repr(v)


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
            'ref': 'Foo',
            'type': 'typed-dict',
            'fields': {
                'height': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                'bar': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'ref': 'Bar',
                        'type': 'typed-dict',
                        'fields': {
                            'width': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                            'bars': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'list',
                                        'items_schema': {'type': 'definition-ref', 'schema_ref': 'Bar'},
                                    },
                                    'default': None,
                                },
                            },
                            'foo': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'union',
                                        'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Foo'}],
                                    },
                                    'default': None,
                                },
                            },
                        },
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
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        # these are here just as decoration
        width: int
        branch: Optional['Branch']

    v = SchemaValidator(
        {
            'type': 'model',
            'ref': 'Branch',
            'cls': Branch,
            'schema': {
                'type': 'model-fields',
                'fields': {
                    'width': {'type': 'model-field', 'schema': {'type': 'int'}},
                    'branch': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'union',
                                'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Branch'}],
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
    assert m1.__pydantic_fields_set__ == {'width'}
    assert m1.__dict__ == {'width': 1, 'branch': None}
    assert m1.width == 1
    assert m1.branch is None

    m2: Branch = v.validate_python({'width': '10', 'branch': {'width': 20}})
    assert isinstance(m2, Branch)
    assert m2.__pydantic_fields_set__ == {'width', 'branch'}
    assert m2.width == 10
    assert isinstance(m2.branch, Branch)
    assert m2.branch.width == 20
    assert m2.branch.branch is None


def test_invalid_schema():
    with pytest.raises(SchemaError, match='Definitions error: attempted to use `Branch` before it was filled'):
        SchemaValidator(
            {
                'type': 'list',
                'items_schema': {
                    'type': 'typed-dict',
                    'fields': {
                        'width': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                        'branch': {
                            'type': 'typed-dict-field',
                            'schema': {
                                'type': 'default',
                                'schema': {
                                    'type': 'nullable',
                                    'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                },
                                'default': None,
                            },
                        },
                    },
                },
            }
        )


def test_outside_parent():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'tuple1': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'tuple-positional',
                        'items_schema': [{'type': 'int'}, {'type': 'int'}, {'type': 'str'}],
                        'ref': 'tuple-iis',
                    },
                },
                'tuple2': {'type': 'typed-dict-field', 'schema': {'type': 'definition-ref', 'schema_ref': 'tuple-iis'}},
            },
        }
    )

    assert v.validate_python({'tuple1': [1, '1', 'frog'], 'tuple2': [2, '2', 'toad']}) == {
        'tuple1': (1, 1, 'frog'),
        'tuple2': (2, 2, 'toad'),
    }


def test_recursion_branch():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'branch': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                        'default': None,
                    },
                },
            },
        },
        {'from_attributes': True},
    )
    assert ',definitions=[TypedDict(TypedDictValidator{' in plain_repr(v)

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'branch': None}
    assert v.validate_python({'name': 'root', 'branch': {'name': 'b1', 'branch': None}}) == {
        'name': 'root',
        'branch': {'name': 'b1', 'branch': None},
    }

    b = {'name': 'recursive'}
    b['branch'] = b
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(b)
    assert exc_info.value.title == 'typed-dict'
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('branch',),
            'msg': 'Recursion error - cyclic reference detected',
            'input': {'name': 'recursive', 'branch': IsPartialDict(name='recursive')},
        }
    ]


def test_recursion_branch_from_attributes():
    v = SchemaValidator(
        {
            'type': 'model-fields',
            'ref': 'Branch',
            'fields': {
                'name': {'type': 'model-field', 'schema': {'type': 'str'}},
                'branch': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                        'default': None,
                    },
                },
            },
        },
        {'from_attributes': True},
    )

    assert v.validate_python({'name': 'root'}) == ({'name': 'root', 'branch': None}, None, {'name'})
    model_dict, model_extra, fields_set = v.validate_python({'name': 'root', 'branch': {'name': 'b1', 'branch': None}})
    assert model_dict == {'name': 'root', 'branch': ({'name': 'b1', 'branch': None}, None, {'name', 'branch'})}
    assert model_extra is None
    assert fields_set == {'name', 'branch'}

    data = Cls(name='root')
    data.branch = Cls(name='b1', branch=None)
    model_dict, model_extra, fields_set = v.validate_python(data)
    assert model_dict == {'name': 'root', 'branch': ({'name': 'b1', 'branch': None}, None, {'name', 'branch'})}
    assert model_extra is None
    assert fields_set == {'name', 'branch'}

    data = Cls(name='root')
    data.branch = data
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('branch',),
            'msg': 'Recursion error - cyclic reference detected',
            'input': HasAttributes(name='root', branch=AnyThing()),
        }
    ]


def test_definition_list():
    v = SchemaValidator(
        {'type': 'list', 'ref': 'the-list', 'items_schema': {'type': 'definition-ref', 'schema_ref': 'the-list'}}
    )
    assert ',definitions=[List(ListValidator{' in plain_repr(v)
    assert v.validate_python([]) == []
    assert v.validate_python([[]]) == [[]]

    data = list()
    data.append(data)
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(data)
    assert exc_info.value.title == 'list[...]'
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': (0,),
            'msg': 'Recursion error - cyclic reference detected',
            'input': [IsList(length=1)],
        }
    ]


@pytest.fixture(scope='module')
def multiple_tuple_schema() -> SchemaValidator:
    return SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'f1': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'tuple-positional',
                        'items_schema': [
                            {'type': 'int'},
                            {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 't'}},
                        ],
                        'ref': 't',
                    },
                },
                'f2': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 't'}},
                        'default': None,
                    },
                },
            },
        }
    )


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'f1': [1, None]}, {'f1': (1, None), 'f2': None}),
        ({'f1': [1, None], 'f2': [2, None]}, {'f1': (1, None), 'f2': (2, None)}),
        (
            {'f1': [1, (3, None)], 'f2': [2, (4, (4, (5, None)))]},
            {'f1': (1, (3, None)), 'f2': (2, (4, (4, (5, None))))},
        ),
        ({'f1': [1, 2]}, Err(r'f1.1\s+Input should be a valid tuple')),
        ({'f1': [1, (3, None)], 'f2': [2, (4, (4, (5, 6)))]}, Err(r'f2.1.1.1.1\s+Input should be a valid tuple')),
    ],
)
def test_multiple_tuple_param(multiple_tuple_schema: SchemaValidator, input_value, expected):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            multiple_tuple_schema.validate_python(input_value)
        # debug(repr(exc_info.value))
    else:
        assert multiple_tuple_schema.validate_python(input_value) == expected


def test_multiple_tuple_repeat(multiple_tuple_schema: SchemaValidator):
    t = (42, None)
    assert multiple_tuple_schema.validate_python({'f1': (1, t), 'f2': (2, t)}) == {
        'f1': (1, (42, None)),
        'f2': (2, (42, None)),
    }


def test_multiple_tuple_recursion(multiple_tuple_schema: SchemaValidator):
    data = [1]
    data.append(data)
    with pytest.raises(ValidationError) as exc_info:
        multiple_tuple_schema.validate_python({'f1': data, 'f2': data})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('f1', 1),
            'msg': 'Recursion error - cyclic reference detected',
            'input': [1, IsList(length=2)],
        },
        {
            'type': 'recursion_loop',
            'loc': ('f2', 1),
            'msg': 'Recursion error - cyclic reference detected',
            'input': [1, IsList(length=2)],
        },
    ]


def test_multiple_tuple_recursion_once(multiple_tuple_schema: SchemaValidator):
    data = [1]
    data.append(data)
    with pytest.raises(ValidationError) as exc_info:
        multiple_tuple_schema.validate_python({'f1': data, 'f2': data})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('f1', 1),
            'msg': 'Recursion error - cyclic reference detected',
            'input': [1, IsList(length=2)],
        },
        {
            'type': 'recursion_loop',
            'loc': ('f2', 1),
            'msg': 'Recursion error - cyclic reference detected',
            'input': [1, IsList(length=2)],
        },
    ]


def test_definition_wrap():
    def wrap_func(input_value, validator, info):
        return validator(input_value) + (42,)

    v = SchemaValidator(
        {
            'type': 'function-wrap',
            'ref': 'wrapper',
            'function': {'type': 'general', 'function': wrap_func},
            'schema': {
                'type': 'tuple-positional',
                'items_schema': [
                    {'type': 'int'},
                    {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'wrapper'}},
                ],
            },
        }
    )
    assert v.validate_python((1, None)) == (1, None, 42)
    assert v.validate_python((1, (2, (3, None)))) == (1, (2, (3, None, 42), 42), 42)
    t = [1]
    t.append(t)
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(t)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': (1,),
            'msg': 'Recursion error - cyclic reference detected',
            'input': IsList(positions={0: 1}, length=2),
        }
    ]


def test_union_ref_strictness():
    v = SchemaValidator(
        {
            'fields': {
                'a': {'type': 'typed-dict-field', 'schema': {'type': 'int', 'ref': 'int-type'}},
                'b': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'union',
                        'choices': [{'type': 'definition-ref', 'schema_ref': 'int-type'}, {'type': 'str'}],
                    },
                },
            },
            'type': 'typed-dict',
        }
    )
    assert v.validate_python({'a': 1, 'b': '2'}) == {'a': 1, 'b': '2'}
    assert v.validate_python({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': []})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('b', 'int'), 'msg': 'Input should be a valid integer', 'input': []},
        {'type': 'string_type', 'loc': ('b', 'str'), 'msg': 'Input should be a valid string', 'input': []},
    ]


def test_union_container_strictness():
    v = SchemaValidator(
        {
            'fields': {
                'b': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'union', 'choices': [{'type': 'int', 'ref': 'int-type'}, {'type': 'str'}]},
                },
                'a': {'type': 'typed-dict-field', 'schema': {'type': 'definition-ref', 'schema_ref': 'int-type'}},
            },
            'type': 'typed-dict',
        }
    )
    assert v.validate_python({'a': 1, 'b': '2'}) == {'a': 1, 'b': '2'}
    assert v.validate_python({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': []})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('b', 'int'), 'msg': 'Input should be a valid integer', 'input': []},
        {'type': 'string_type', 'loc': ('b', 'str'), 'msg': 'Input should be a valid string', 'input': []},
    ]


@pytest.mark.parametrize('strict', [True, False], ids=lambda s: f'strict={s}')
def test_union_cycle(strict: bool):
    s = SchemaValidator(
        {
            'choices': [
                {
                    'fields': {
                        'foobar': {
                            'type': 'typed-dict-field',
                            'schema': {
                                'items_schema': {'schema_ref': 'root-schema', 'type': 'definition-ref'},
                                'type': 'list',
                            },
                        }
                    },
                    'type': 'typed-dict',
                }
            ],
            'auto_collapse': False,
            'strict': strict,
            'ref': 'root-schema',
            'type': 'union',
        }
    )

    data = {'foobar': []}
    data['foobar'].append(data)

    with pytest.raises(ValidationError) as exc_info:
        s.validate_python(data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('typed-dict', 'foobar', 0),
            'msg': 'Recursion error - cyclic reference detected',
            'input': {'foobar': [{'foobar': IsList(length=1)}]},
        }
    ]


def test_function_name():
    def f(input_value, info):
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'choices': [
                {
                    'type': 'function-after',
                    'function': {'type': 'general', 'function': f},
                    'schema': {'schema_ref': 'root-schema', 'type': 'definition-ref'},
                },
                {'type': 'int'},
            ],
            'ref': 'root-schema',
            'type': 'union',
        }
    )

    assert v.validate_python(123) == 123

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': ('function-after[f(), ...]',),
            'msg': 'Recursion error - cyclic reference detected',
            'input': 'input value',
        },
        {
            'type': 'int_parsing',
            'loc': ('int',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'input value',
        },
    ]


@pytest.mark.skipif(
    platform.python_implementation() == 'PyPy' and pydantic_core._pydantic_core.build_profile == 'debug',
    reason='PyPy does not have enough stack space for Rust debug builds to recurse very deep',
)
@pytest.mark.parametrize('strict', [True, False], ids=lambda s: f'strict={s}')
def test_function_change_id(strict: bool):
    def f(input_value, info):
        _, count = input_value.split('-')
        return f'f-{int(count) + 1}'

    v = SchemaValidator(
        {
            'choices': [
                {
                    'type': 'function-before',
                    'function': {'type': 'general', 'function': f},
                    'schema': {'schema_ref': 'root-schema', 'type': 'definition-ref'},
                }
            ],
            'auto_collapse': False,
            'strict': strict,
            'ref': 'root-schema',
            'type': 'union',
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('start-0')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'recursion_loop',
            'loc': IsTuple(length=(1, 255)),
            'msg': 'Recursion error - cyclic reference detected',
            'input': IsStr(regex=r'f-\d+'),
        }
    ]


def test_many_uses_of_ref():
    # check we can safely exceed RECURSION_GUARD_LIMIT without upsetting the recursion guard
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'str', 'max_length': 8, 'ref': 'limited-string'},
                },
                'other_names': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'list',
                        'items_schema': {'type': 'definition-ref', 'schema_ref': 'limited-string'},
                    },
                },
            },
        }
    )

    assert v.validate_python({'name': 'Anne', 'other_names': ['Bob', 'Charlie']}) == {
        'name': 'Anne',
        'other_names': ['Bob', 'Charlie'],
    }

    with pytest.raises(ValidationError, match=r'other_names.2\s+String should have at most 8 characters'):
        v.validate_python({'name': 'Anne', 'other_names': ['Bob', 'Charlie', 'Daveeeeee']})

    long_input = {'name': 'Anne', 'other_names': [f'p-{i}' for i in range(300)]}
    assert v.validate_python(long_input) == long_input


def test_error_inside_definition_wrapper():
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator(
            {
                'type': 'typed-dict',
                'ref': 'Branch',
                'fields': {
                    'sub_branch': {
                        'type': 'typed-dict-field',
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'nullable',
                                'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                            },
                            'default': None,
                            'default_factory': lambda x: 'foobar',
                        },
                    }
                },
            }
        )
    assert str(exc_info.value) == (
        'Field "sub_branch":\n'
        '  SchemaError: Error building "default" validator:\n'
        "  SchemaError: 'default' and 'default_factory' cannot be used together"
    )


def test_recursive_definitions_schema(pydantic_version) -> None:
    s = core_schema.definitions_schema(
        core_schema.definition_reference_schema(schema_ref='a'),
        [
            core_schema.typed_dict_schema(
                {
                    'b': core_schema.typed_dict_field(
                        core_schema.list_schema(core_schema.definition_reference_schema('b'))
                    )
                },
                ref='a',
            ),
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(
                        core_schema.list_schema(core_schema.definition_reference_schema('a'))
                    )
                },
                ref='b',
            ),
        ],
    )

    v = SchemaValidator(s)

    assert v.validate_python({'b': [{'a': []}]}) == {'b': [{'a': []}]}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'b': [{'a': {}}]})

    assert exc_info.value.errors() == [
        {
            'type': 'list_type',
            'loc': ('b', 0, 'a'),
            'msg': 'Input should be a valid list',
            'input': {},
            'url': f'https://errors.pydantic.dev/{pydantic_version}/v/list_type',
        }
    ]


def test_unsorted_definitions_schema() -> None:
    s = core_schema.definitions_schema(
        core_schema.definition_reference_schema(schema_ref='td'),
        [
            core_schema.typed_dict_schema(
                {'x': core_schema.typed_dict_field(core_schema.definition_reference_schema('int'))}, ref='td'
            ),
            core_schema.int_schema(ref='int'),
        ],
    )

    v = SchemaValidator(s)

    assert v.validate_python({'x': 123}) == {'x': 123}

    with pytest.raises(ValidationError):
        v.validate_python({'x': 'abc'})


def test_validate_assignment(pydantic_version) -> None:
    @dataclass
    class Model:
        x: List['Model']

    schema = core_schema.dataclass_schema(
        Model,
        core_schema.dataclass_args_schema(
            'Model',
            [
                core_schema.dataclass_field(
                    name='x',
                    schema=core_schema.list_schema(core_schema.definition_reference_schema('model')),
                    kw_only=False,
                )
            ],
        ),
        ['x'],
        ref='model',
        config=core_schema.CoreConfig(revalidate_instances='always'),
    )
    v = SchemaValidator(schema)

    data = [Model(x=[Model(x=[])])]
    instance = Model(x=[])
    v.validate_assignment(instance, 'x', data)
    assert instance.x == data

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(instance, 'x', [Model(x=[Model(x=[Model(x=[123])])])])

    assert exc_info.value.errors() == [
        {
            'type': 'dataclass_type',
            'loc': ('x', 0, 'x', 0, 'x', 0, 'x', 0),
            'msg': 'Input should be a dictionary or an instance of Model',
            'input': 123,
            'ctx': {'class_name': 'Model'},
            'url': f'https://errors.pydantic.dev/{pydantic_version}/v/dataclass_type',
        }
    ]
