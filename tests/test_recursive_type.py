import pytest
from pydantic_core import ValidationError
from typing_extensions import Annotated, TypeAlias

from pydantic import BaseModel, RecursiveType

Json: TypeAlias = list['Json'] | dict[str, 'Json'] | str | int | float | bool | None


def test_recursive_type():
    class Model(BaseModel):
        x: Annotated[Json, RecursiveType('Json')]

    assert Model(x=[1, 2, 3]).x == [1, 2, 3]

    assert Model(x={'a': [1, {'b': 3}]}).x == {'a': [1, {'b': 3}]}

    with pytest.raises(ValidationError) as exc_info:
        Model(x={'a': [1, {'b': 3}, ...]})
    assert exc_info.value.errors() == [
        {
            'input': {'a': [1, {'b': 3}, Ellipsis]},
            'loc': ('x', 'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]'),
            'msg': 'Input should be a valid list',
            'type': 'list_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'list[nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
            ),
            'msg': 'Input should be a valid list',
            'type': 'list_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
            ),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'str',
            ),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'int',
            ),
            'msg': 'Input should be a valid integer',
            'type': 'int_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'float',
            ),
            'msg': 'Input should be a valid number',
            'type': 'float_type',
        },
        {
            'input': Ellipsis,
            'loc': (
                'x',
                'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]',
                'a',
                'list[nullable[union[list[nullable[union[list[...],dict[str,...],str,int,float,bool]]],dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]],str,int,float,bool]]]',
                2,
                'bool',
            ),
            'msg': 'Input should be a valid boolean',
            'type': 'bool_type',
        },
        {
            'input': [1, {'b': 3}, Ellipsis],
            'loc': ('x', 'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 'a', 'dict[str,...]'),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
        {
            'input': [1, {'b': 3}, Ellipsis],
            'loc': ('x', 'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 'a', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': [1, {'b': 3}, Ellipsis],
            'loc': ('x', 'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 'a', 'int'),
            'msg': 'Input should be a valid integer',
            'type': 'int_type',
        },
        {
            'input': [1, {'b': 3}, Ellipsis],
            'loc': ('x', 'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 'a', 'float'),
            'msg': 'Input should be a valid number',
            'type': 'float_type',
        },
        {
            'input': [1, {'b': 3}, Ellipsis],
            'loc': ('x', 'dict[str,nullable[union[list[...],dict[str,...],str,int,float,bool]]]', 'a', 'bool'),
            'msg': 'Input should be a valid boolean',
            'type': 'bool_type',
        },
        {
            'input': {'a': [1, {'b': 3}, Ellipsis]},
            'loc': ('x', 'str'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        },
        {
            'input': {'a': [1, {'b': 3}, Ellipsis]},
            'loc': ('x', 'int'),
            'msg': 'Input should be a valid integer',
            'type': 'int_type',
        },
        {
            'input': {'a': [1, {'b': 3}, Ellipsis]},
            'loc': ('x', 'float'),
            'msg': 'Input should be a valid number',
            'type': 'float_type',
        },
        {
            'input': {'a': [1, {'b': 3}, Ellipsis]},
            'loc': ('x', 'bool'),
            'msg': 'Input should be a valid boolean',
            'type': 'bool_type',
        },
    ]
