from typing import Optional

import pytest
from dirty_equals import AnyThing, HasAttributes, IsInstance, IsList, IsPartialDict, IsStr, IsTuple

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, plain_repr
from .test_typed_dict import Cls


def test_branch_nullable():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'schema': {'type': 'str'}},
                'sub_branch': {
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                        'default': None,
                    }
                },
            },
        }
    )
    assert 'return_fields_set:false' in plain_repr(v)

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'sub_branch': None}
    assert plain_repr(v).startswith('SchemaValidator(name="typed-dict",validator=DefinitionRef(DefinitionRefValidator{')
    assert ',slots=[TypedDict(TypedDictValidator{' in plain_repr(v)

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
                        'name': {'schema': {'type': 'str'}},
                        'sub_branch': {
                            'schema': {
                                'type': 'default',
                                'schema': {
                                    'type': 'nullable',
                                    'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                },
                                'default': None,
                            }
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
    assert ',slots=[TypedDict(TypedDictValidator{' in plain_repr(v)


def test_unused_ref():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {'name': {'schema': {'type': 'str'}}, 'other': {'schema': {'type': 'int'}}},
        }
    )
    assert plain_repr(v).startswith('SchemaValidator(name="typed-dict",validator=TypedDict(TypedDictValidator')
    assert v.validate_python({'name': 'root', 'other': '4'}) == {'name': 'root', 'other': 4}
    assert ',slots=[]' in plain_repr(v)


def test_nullable_error():
    v = SchemaValidator(
        {
            'ref': 'Branch',
            'type': 'typed-dict',
            'fields': {
                'width': {'schema': {'type': 'int'}},
                'sub_branch': {
                    'schema': {
                        'type': 'default',
                        'schema': {
                            'type': 'union',
                            'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Branch'}],
                        },
                        'default': None,
                    }
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
            'type': 'none_required',
            'loc': ('sub_branch', 'none'),
            'msg': 'Input should be None/null',
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
                'width': {'schema': {'type': 'int'}},
                'branches': {
                    'schema': {
                        'type': 'default',
                        'schema': {
                            'type': 'list',
                            'items_schema': {'type': 'definition-ref', 'schema_ref': 'BranchList'},
                        },
                        'default': None,
                    }
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
    assert ',slots=[TypedDict(TypedDictValidator{' in plain_repr(v)


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
                'height': {'schema': {'type': 'int'}},
                'bar': {
                    'schema': {
                        'ref': 'Bar',
                        'type': 'typed-dict',
                        'fields': {
                            'width': {'schema': {'type': 'int'}},
                            'bars': {
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'list',
                                        'items_schema': {'type': 'definition-ref', 'schema_ref': 'Bar'},
                                    },
                                    'default': None,
                                }
                            },
                            'foo': {
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'union',
                                        'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Foo'}],
                                    },
                                    'default': None,
                                }
                            },
                        },
                    }
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
        branch: Optional['Branch']

    v = SchemaValidator(
        {
            'type': 'model',
            'ref': 'Branch',
            'cls': Branch,
            'schema': {
                'type': 'typed-dict',
                'return_fields_set': True,
                'fields': {
                    'width': {'schema': {'type': 'int'}},
                    'branch': {
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'union',
                                'choices': [{'type': 'none'}, {'type': 'definition-ref', 'schema_ref': 'Branch'}],
                            },
                            'default': None,
                        }
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
    with pytest.raises(SchemaError, match="Slots Error: ref 'Branch' not found"):
        SchemaValidator(
            {
                'type': 'list',
                'items_schema': {
                    'type': 'typed-dict',
                    'fields': {
                        'width': {'schema': {'type': 'int'}},
                        'branch': {
                            'schema': {
                                'type': 'default',
                                'schema': {
                                    'type': 'nullable',
                                    'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                },
                                'default': None,
                            }
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
                    'schema': {
                        'type': 'tuple',
                        'mode': 'positional',
                        'items_schema': [{'type': 'int'}, {'type': 'int'}, {'type': 'str'}],
                        'ref': 'tuple-iis',
                    }
                },
                'tuple2': {'schema': {'type': 'definition-ref', 'schema_ref': 'tuple-iis'}},
            },
        }
    )

    assert v.validate_python({'tuple1': [1, '1', 'frog'], 'tuple2': [2, '2', 'toad']}) == {
        'tuple1': (1, 1, 'frog'),
        'tuple2': (2, 2, 'toad'),
    }
    # the definition goes into reusable and gets "inlined" into the schema
    assert ',slots=[]' in plain_repr(v)


def test_recursion_branch():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'schema': {'type': 'str'}},
                'branch': {
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'}},
                        'default': None,
                    }
                },
            },
        },
        {'from_attributes': True},
    )
    assert ',slots=[TypedDict(TypedDictValidator{' in plain_repr(v)

    assert v.validate_python({'name': 'root'}) == {'name': 'root', 'branch': None}
    assert v.validate_python({'name': 'root', 'branch': {'name': 'b1', 'branch': None}}) == {
        'name': 'root',
        'branch': {'name': 'b1', 'branch': None},
    }

    data = Cls(name='root')
    data.branch = Cls(name='b1', branch=None)
    assert v.validate_python(data) == {'name': 'root', 'branch': {'name': 'b1', 'branch': None}}

    b = {'name': 'recursive'}
    b['branch'] = b
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(b)
    assert exc_info.value.title == 'typed-dict'
    assert exc_info.value.errors() == [
        {
            'type': 'recursion_loop',
            'loc': ('branch',),
            'msg': 'Recursion error - cyclic reference detected',
            'input': {'name': 'recursive', 'branch': IsPartialDict(name='recursive')},
        }
    ]

    data = Cls(name='root')
    data.branch = data
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(data)
    assert exc_info.value.errors() == [
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
    assert ',slots=[List(ListValidator{' in plain_repr(v)
    assert v.validate_python([]) == []
    assert v.validate_python([[]]) == [[]]

    data = list()
    data.append(data)
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(data)
    assert exc_info.value.title == 'list[...]'
    assert exc_info.value.errors() == [
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
                    'schema': {
                        'type': 'tuple',
                        'mode': 'positional',
                        'items_schema': [
                            {'type': 'int'},
                            {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 't'}},
                        ],
                        'ref': 't',
                    }
                },
                'f2': {
                    'schema': {
                        'type': 'default',
                        'schema': {'type': 'nullable', 'schema': {'type': 'definition-ref', 'schema_ref': 't'}},
                        'default': None,
                    }
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
        ({'f1': [1, 2]}, Err(r'f1 -> 1\s+Input should be a valid tuple')),
        (
            {'f1': [1, (3, None)], 'f2': [2, (4, (4, (5, 6)))]},
            Err(r'f2 -> 1 -> 1 -> 1 -> 1\s+Input should be a valid tuple'),
        ),
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

    assert exc_info.value.errors() == [
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

    assert exc_info.value.errors() == [
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
    def wrap_func(input_value, *, validator, **kwargs):
        return validator(input_value) + (42,)

    v = SchemaValidator(
        {
            'type': 'function',
            'ref': 'wrapper',
            'mode': 'wrap',
            'function': wrap_func,
            'schema': {
                'type': 'tuple',
                'mode': 'positional',
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
    assert exc_info.value.errors() == [
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
                'a': {'schema': {'type': 'int', 'ref': 'int-type'}},
                'b': {
                    'schema': {
                        'type': 'union',
                        'choices': [{'type': 'definition-ref', 'schema_ref': 'int-type'}, {'type': 'str'}],
                    }
                },
            },
            'type': 'typed-dict',
        }
    )
    assert v.validate_python({'a': 1, 'b': '2'}) == {'a': 1, 'b': '2'}
    assert v.validate_python({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': []})

    assert exc_info.value.errors() == [
        {'type': 'int_type', 'loc': ('b', 'int'), 'msg': 'Input should be a valid integer', 'input': []},
        {'type': 'string_type', 'loc': ('b', 'str'), 'msg': 'Input should be a valid string', 'input': []},
    ]


def test_union_container_strictness():
    v = SchemaValidator(
        {
            'fields': {
                'b': {'schema': {'type': 'union', 'choices': [{'type': 'int', 'ref': 'int-type'}, {'type': 'str'}]}},
                'a': {'schema': {'type': 'definition-ref', 'schema_ref': 'int-type'}},
            },
            'type': 'typed-dict',
        }
    )
    assert v.validate_python({'a': 1, 'b': '2'}) == {'a': 1, 'b': '2'}
    assert v.validate_python({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': []})

    assert exc_info.value.errors() == [
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
                            'schema': {
                                'items_schema': {'schema_ref': 'root-schema', 'type': 'definition-ref'},
                                'type': 'list',
                            }
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
    assert exc_info.value.errors() == [
        {
            'type': 'recursion_loop',
            'loc': ('typed-dict', 'foobar', 0),
            'msg': 'Recursion error - cyclic reference detected',
            'input': {'foobar': [{'foobar': IsList(length=1)}]},
        }
    ]


def test_function_name():
    def f(input_value, **kwargs):
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'choices': [
                {
                    'type': 'function',
                    'mode': 'after',
                    'function': f,
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

    assert exc_info.value.errors() == [
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


@pytest.mark.parametrize('strict', [True, False], ids=lambda s: f'strict={s}')
def test_function_change_id(strict: bool):
    def f(input_value, **kwargs):
        _, count = input_value.split('-')
        return f'f-{int(count) + 1}'

    v = SchemaValidator(
        {
            'choices': [
                {
                    'type': 'function',
                    'mode': 'before',
                    'function': f,
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

    assert exc_info.value.errors() == [
        {
            'type': 'recursion_loop',
            'loc': IsTuple(length=(1, 255)),
            'msg': 'Recursion error - cyclic reference detected',
            'input': IsStr(regex=r'f-\d+'),
        }
    ]


def test_many_uses_of_ref():
    # check we can safely exceed BACKUP_GUARD_LIMIT without upsetting the backup recursion guard
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': 'Branch',
            'fields': {
                'name': {'schema': {'type': 'str', 'max_length': 8, 'ref': 'limited-string'}},
                'other_names': {
                    'schema': {
                        'type': 'list',
                        'items_schema': {'type': 'definition-ref', 'schema_ref': 'limited-string'},
                    }
                },
            },
        }
    )

    assert v.validate_python({'name': 'Anne', 'other_names': ['Bob', 'Charlie']}) == {
        'name': 'Anne',
        'other_names': ['Bob', 'Charlie'],
    }

    with pytest.raises(ValidationError, match=r'other_names -> 2\s+String should have at most 8 characters'):
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
                        'schema': {
                            'type': 'default',
                            'schema': {
                                'type': 'nullable',
                                'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                            },
                            'default': None,
                            'default_factory': lambda x: 'foobar',
                        }
                    }
                },
            }
        )
    assert str(exc_info.value) == (
        'Field "sub_branch":\n'
        '  SchemaError: Error building "default" validator:\n'
        "  SchemaError: 'default' and 'default_factory' cannot be used together"
    )


def test_model_td_recursive():
    class Foobar:
        __slots__ = '__dict__', '__fields_set__'

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'ref': '__main__.Foobar',
            'return_fields_set': True,
            'fields': {
                'x': {'schema': {'type': 'int'}, 'required': True},
                'y': {
                    'schema': {
                        'type': 'default',
                        'schema': {
                            'type': 'union',
                            'choices': [
                                {
                                    'type': 'model',
                                    'cls': Foobar,
                                    'schema': {'type': 'definition-ref', 'schema_ref': '__main__.Foobar'},
                                },
                                {'type': 'none'},
                            ],
                        },
                        'default': None,
                    },
                    'required': False,
                },
            },
        }
    )
    assert 'return_fields_set:true' in plain_repr(v)
    d, fields_set = v.validate_python(dict(x=1, y={'x': 2}))
    assert d == {'x': 1, 'y': IsInstance(Foobar)}
    assert fields_set == {'y', 'x'}

    f = d['y']
    assert isinstance(f, Foobar)
    assert f.x == 2
    assert f.y is None
    assert f.__fields_set__ == {'x'}
