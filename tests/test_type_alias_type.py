from typing import Dict, List, TypeVar, Union

import pytest
from annotated_types import MaxLen
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel, ValidationError

T = TypeVar('T')

JsonType = TypeAliasType('JsonType', Union[List['JsonType'], Dict[str, 'JsonType'], str, int, float, bool, None])
RecursiveGenericAlias = TypeAliasType(
    'RecursiveGenericAlias', List[Union['RecursiveGenericAlias[T]', T]], type_params=(T,)
)
MyList = TypeAliasType('MyList', List[T], type_params=(T,))
# try mixing with implicit type aliases
ShortMyList = Annotated[MyList[T], MaxLen(1)]
ShortRecursiveGenericAlias = Annotated[RecursiveGenericAlias[T], MaxLen(1)]


def test_type_alias_type() -> None:
    class Model(BaseModel):
        x1: MyList[int]
        x2: ShortMyList[int]
        x3: JsonType
        x4: RecursiveGenericAlias[int]
        x5: ShortRecursiveGenericAlias[int]

    assert Model(x1=[1, 2], x2=[1], x3=[{'a': [1, 2]}], x4=[1], x5=[[1]]).model_dump() == {
        'x1': [1, 2],
        'x2': [1],
        'x3': [{'a': [1, 2]}],
        'x4': [1],
        'x5': [[1]],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 'a'], x2=[1], x3=[{'a': [1, 2]}], x4=[1], x5=[[1]])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x1', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1], x2=['a'], x3=[{'a': [1, 2]}], x4=[1], x5=[[1]])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x2', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1, 2, 3, 4, 5], x3=[{'a': [1, 2]}], x4=[1], x5=[[1]])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('x2',),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2, 3, 4, 5],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1], x3=[{('not valid', 'tuple'): [1, 2]}], x4=[1], x5=[[1]])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': (
                'x3',
                'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                0,
                'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
            ),
            'msg': 'Input should be a valid list',
            'input': {('not valid', 'tuple'): [1, 2]},
        },
        {
            'type': 'string_type',
            'loc': (
                'x3',
                'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                0,
                'dict[str,...]',
                "('not valid', 'tuple')",
                '[key]',
            ),
            'msg': 'Input should be a valid string',
            'input': ('not valid', 'tuple'),
        },
        {
            'type': 'string_type',
            'loc': ('x3', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 0, 'str'),
            'msg': 'Input should be a valid string',
            'input': {('not valid', 'tuple'): [1, 2]},
        },
        {
            'type': 'int_type',
            'loc': ('x3', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': {('not valid', 'tuple'): [1, 2]},
        },
        {
            'type': 'float_type',
            'loc': ('x3', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 0, 'float'),
            'msg': 'Input should be a valid number',
            'input': {('not valid', 'tuple'): [1, 2]},
        },
        {
            'type': 'bool_type',
            'loc': ('x3', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 0, 'bool'),
            'msg': 'Input should be a valid boolean',
            'input': {('not valid', 'tuple'): [1, 2]},
        },
        {
            'type': 'dict_type',
            'loc': ('x3', 'dict[str,...]'),
            'msg': 'Input should be a valid dictionary',
            'input': [{('not valid', 'tuple'): [1, 2]}],
        },
        {
            'type': 'string_type',
            'loc': ('x3', 'str'),
            'msg': 'Input should be a valid string',
            'input': [{('not valid', 'tuple'): [1, 2]}],
        },
        {
            'type': 'int_type',
            'loc': ('x3', 'int'),
            'msg': 'Input should be a valid integer',
            'input': [{('not valid', 'tuple'): [1, 2]}],
        },
        {
            'type': 'float_type',
            'loc': ('x3', 'float'),
            'msg': 'Input should be a valid number',
            'input': [{('not valid', 'tuple'): [1, 2]}],
        },
        {
            'type': 'bool_type',
            'loc': ('x3', 'bool'),
            'msg': 'Input should be a valid boolean',
            'input': [{('not valid', 'tuple'): [1, 2]}],
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1], x3=[{'a': [1, 2]}], x4=[[[[['a']]]]], x5=[[1]])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': (
                'x4',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
            ),
            'msg': 'Input should be a valid list',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (
                'x4',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'list[union[...,int]]',
                0,
                'int',
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_type',
            'loc': ('x4', 0, 'list[union[...,int]]', 0, 'list[union[...,int]]', 0, 'list[union[...,int]]', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': ['a'],
        },
        {
            'type': 'int_type',
            'loc': ('x4', 0, 'list[union[...,int]]', 0, 'list[union[...,int]]', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': [['a']],
        },
        {
            'type': 'int_type',
            'loc': ('x4', 0, 'list[union[...,int]]', 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': [[['a']]],
        },
        {'type': 'int_type', 'loc': ('x4', 0, 'int'), 'msg': 'Input should be a valid integer', 'input': [[[['a']]]]},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1], x3=[{'a': [1, 2]}], x4=[[[[[1]]]]], x5=['a'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('x5', 0, 'list[union[...,int]]'),
            'msg': 'Input should be a valid list',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('x5', 0, 'int'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
    ]

    # insert_assert(Model.model_json_schema())
