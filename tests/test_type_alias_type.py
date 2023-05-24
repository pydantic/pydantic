from typing import Any, Dict, ForwardRef, List, Set, TypeVar, Union

import pytest
from typing_extensions import Annotated, TypeAliasType

from pydantic import BaseModel, ValidationError
from pydantic.functional_validators import AfterValidator

T = TypeVar('T')

JsonType = TypeAliasType(
    'JsonType', Union[List[ForwardRef('JsonType')], Dict[str, ForwardRef('JsonType')], str, int, float, bool, None]
)
RecursiveGenericAlias = TypeAliasType(
    'RecursiveGenericAlias', List[Union[ForwardRef('RecursiveGenericAlias[T]'), T]], type_params=(T,)
)


def test_type_alias_type() -> None:
    ListOrSet = TypeAliasType('ListOrSet', Union[List[T], Set[T]], type_params=(T,))

    def check_short(x: Any) -> Any:
        assert len(x) <= 1
        return x

    ShortListOrSet = TypeAliasType(
        'ShortListOrSet', Annotated[ListOrSet[T], AfterValidator(check_short)], type_params=(T,)
    )

    class Model(BaseModel):
        x1: ListOrSet[int]
        x2: ShortListOrSet[int]
        x3: JsonType
        x4: RecursiveGenericAlias[int]

    assert Model(x1=[1, 2], x2=[1], x3=[{'a': [1, 2]}], x4=[1]).model_dump() == {
        'x1': [1, 2],
        'x2': [1],
        'x3': [{'a': [1, 2]}],
        'x4': [1],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 'a'], x2=[1], x3=[{'a': [1, 2]}], x4=[1])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x1', 'list[int]', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('x1', 'set[int]', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1, 2, 3, 4, 5], x3=[{'a': [1, 2]}], x4=[1])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'assertion_error',
            'loc': ('x2',),
            'msg': 'Assertion failed, assert 5 <= 1\n +  where 5 = len([1, 2, 3, 4, 5])',
            'input': [1, 2, 3, 4, 5],
            'ctx': {'error': 'assert 5 <= 1\n +  where 5 = len([1, 2, 3, 4, 5])'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(x1=[1, 2], x2=[1], x3=[{('not valid', 'tuple'): [1, 2]}], x4=[1])
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
        Model(x1=[1, 2], x2=[1], x3=[{'a': [1, 2]}], x4=[[[[['a']]]]])
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

    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {
            'x1': {'$ref': '#/$defs/ListOrSet__class__int___'},
            'x2': {'$ref': '#/$defs/ShortListOrSet__class__int___'},
            'x3': {'$ref': '#/$defs/JsonType'},
            'x4': {'$ref': '#/$defs/RecursiveGenericAlias__class__int___'},
        },
        'required': ['x1', 'x2', 'x3', 'x4'],
        'title': 'Model',
        '$defs': {
            'ListOrSet__class__int___': {
                'anyOf': [
                    {'type': 'array', 'items': {'type': 'integer'}},
                    {'type': 'array', 'uniqueItems': True, 'items': {'type': 'integer'}},
                ]
            },
            'ListOrSet__T_': {
                'anyOf': [
                    {'type': 'array', 'items': {'type': 'integer'}},
                    {'type': 'array', 'uniqueItems': True, 'items': {'type': 'integer'}},
                ]
            },
            'ShortListOrSet__class__int___': {'$ref': '#/$defs/ListOrSet__T_'},
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
            },
            'RecursiveGenericAlias__class__int___': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias__class__int___'}, {'type': 'integer'}]},
            },
        },
    }
