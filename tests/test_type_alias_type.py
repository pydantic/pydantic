import datetime
from typing import Dict, List, Tuple, TypeVar, Union

import pytest
from annotated_types import MaxLen
from typing_extensions import Annotated, TypeAliasType

from pydantic import Field, ValidationError
from pydantic.type_adapter import TypeAdapter

T = TypeVar('T')

JsonType = TypeAliasType('JsonType', Union[List['JsonType'], Dict[str, 'JsonType'], str, int, float, bool, None])
RecursiveGenericAlias = TypeAliasType(
    'RecursiveGenericAlias', List[Union['RecursiveGenericAlias[T]', T]], type_params=(T,)
)
MyList = TypeAliasType('MyList', List[T], type_params=(T,))
# try mixing with implicit type aliases
ShortMyList = Annotated[MyList[T], MaxLen(1)]
ShortRecursiveGenericAlias = Annotated[RecursiveGenericAlias[T], MaxLen(1)]


def test_type_alias() -> None:
    t = TypeAdapter(MyList[int])

    assert t.validate_python(['1', '2']) == [1, 2]

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python(['a'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]

    assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}}


def test_recursive_type_alias() -> None:
    t = TypeAdapter(JsonType)

    assert t.validate_python({'a': [True, [{'b': None}]]}) == {'a': [True, [{'b': None}]]}

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python({'a': datetime.date(year=1992, month=12, day=11)})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]',),
            'msg': 'Input should be a valid list',
            'input': {'a': datetime.date(1992, 12, 11)},
        },
        {
            'type': 'list_type',
            'loc': ('dict[str,...]', 'a', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]'),
            'msg': 'Input should be a valid list',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'dict_type',
            'loc': ('dict[str,...]', 'a', 'dict[str,...]'),
            'msg': 'Input should be a valid dictionary',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'string_type',
            'loc': ('dict[str,...]', 'a', 'str'),
            'msg': 'Input should be a valid string',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'int_type',
            'loc': ('dict[str,...]', 'a', 'int'),
            'msg': 'Input should be a valid integer',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'float_type',
            'loc': ('dict[str,...]', 'a', 'float'),
            'msg': 'Input should be a valid number',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'bool_type',
            'loc': ('dict[str,...]', 'a', 'bool'),
            'msg': 'Input should be a valid boolean',
            'input': datetime.date(1992, 12, 11),
        },
        {
            'type': 'string_type',
            'loc': ('str',),
            'msg': 'Input should be a valid string',
            'input': {'a': datetime.date(1992, 12, 11)},
        },
        {
            'type': 'int_type',
            'loc': ('int',),
            'msg': 'Input should be a valid integer',
            'input': {'a': datetime.date(1992, 12, 11)},
        },
        {
            'type': 'float_type',
            'loc': ('float',),
            'msg': 'Input should be a valid number',
            'input': {'a': datetime.date(1992, 12, 11)},
        },
        {
            'type': 'bool_type',
            'loc': ('bool',),
            'msg': 'Input should be a valid boolean',
            'input': {'a': datetime.date(1992, 12, 11)},
        },
    ]

    assert t.json_schema() == {
        'allOf': [{'$ref': '#/$defs/JsonType'}],
        '$defs': {
            'JsonType': {
                'anyOf': [
                    {'type': 'array', 'items': {'$ref': '#/$defs/JsonType'}},
                    {'type': 'object', 'additionalProperties': {'$ref': '#/$defs/JsonType'}},
                    {'type': 'string'},
                    {'type': 'integer'},
                    {'type': 'number'},
                    {'type': 'boolean'},
                    {'type': 'null'},
                ]
            }
        },
    }


def test_type_alias_annotated() -> None:
    t = TypeAdapter(ShortMyList[int])

    assert t.validate_python(['1']) == [1]

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python([1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]

    assert t.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 1}


def test_type_alias_annotated_defs() -> None:
    # force use of refs by referencing the schema in multiple places
    t = TypeAdapter(Tuple[ShortMyList[int], ShortMyList[int]])

    assert t.validate_python((['1'], ['2'])) == ([1], [2])

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python(([1, 2], [1, 2]))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (0,),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        },
        {
            'type': 'too_long',
            'loc': (1,),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        },
    ]

    assert t.json_schema() == {
        'type': 'array',
        'minItems': 2,
        'prefixItems': [
            {'$ref': '#/$defs/MyList_MaxLen_max_length_1_'},
            {'$ref': '#/$defs/MyList_MaxLen_max_length_1_'},
        ],
        'maxItems': 2,
        '$defs': {'MyList_MaxLen_max_length_1_': {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 1}},
    }


def test_recursive_generic_type_alias() -> None:
    t = TypeAdapter(RecursiveGenericAlias[int])

    assert t.validate_python([[['1']]]) == [[[1]]]

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python([[['a']]])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': (0, 'list[union[...,int]]', 0, 'list[union[...,int]]', 0, 'list[union[...,int]]'),
            'msg': 'Input should be a valid list',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (0, 'list[union[...,int]]', 0, 'list[union[...,int]]', 0, 'int'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_type',
            'loc': (0, 'list[union[...,int]]', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': ['a'],
        },
        {'type': 'int_type', 'loc': (0, 'int'), 'msg': 'Input should be a valid integer', 'input': [['a']]},
    ]

    assert t.json_schema() == {
        'allOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}],
        '$defs': {
            'RecursiveGenericAlias': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}, {'type': 'integer'}]},
            }
        },
    }


def test_recursive_generic_type_alias_annotated() -> None:
    t = TypeAdapter(ShortRecursiveGenericAlias[int])

    assert t.validate_python([[]]) == [[]]

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python([[], []])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [[], []],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]

    # insert_assert(t.json_schema())
    assert t.json_schema() == {
        'type': 'array',
        'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}, {'type': 'integer'}]},
        'maxItems': 1,
        '$defs': {
            'RecursiveGenericAlias': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}, {'type': 'integer'}]},
            }
        },
    }


def test_recursive_generic_type_alias_annotated_defs() -> None:
    # force use of refs by referencing the schema in multiple places
    t = TypeAdapter(Tuple[ShortRecursiveGenericAlias[int], ShortRecursiveGenericAlias[int]])

    assert t.validate_python(([[]], [[]])) == ([[]], [[]])

    with pytest.raises(ValidationError) as exc_info:
        t.validate_python(([[], []], [[]]))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (0,),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [[], []],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]

    # insert_assert(t.json_schema())
    assert t.json_schema() == {
        'type': 'array',
        'minItems': 2,
        'prefixItems': [
            {'$ref': '#/$defs/RecursiveGenericAlias_MaxLen_max_length_1_'},
            {'$ref': '#/$defs/RecursiveGenericAlias_MaxLen_max_length_1_'},
        ],
        'maxItems': 2,
        '$defs': {
            'RecursiveGenericAlias': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}, {'type': 'integer'}]},
            },
            'RecursiveGenericAlias_MaxLen_max_length_1_': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias'}, {'type': 'integer'}]},
                'maxItems': 1,
            },
        },
    }


@pytest.mark.xfail(reason='description is currently dropped')
def test_field() -> None:
    SomeAlias = TypeAliasType('SomeAlias', Annotated[int, Field(description='number')])

    ta = TypeAdapter(Annotated[SomeAlias, Field(title='abc')])

    # insert_assert(ta.json_schema())
    assert ta.json_schema() == {
        '$defs': {'SomeAlias': {'type': 'integer', 'description': 'number'}},
        'allOf': [{'$ref': '#/$defs/SomeAlias'}],
        'title': 'abc',
    }
