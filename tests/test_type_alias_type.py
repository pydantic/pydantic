import datetime
import sys
from dataclasses import dataclass
from typing import Dict, Generic, List, Tuple, TypeVar, Union

import pytest
from annotated_types import MaxLen
from typing_extensions import Annotated, Literal, TypeAliasType

from pydantic import BaseModel, Field, PydanticSchemaGenerationError, ValidationError
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
        '$ref': '#/$defs/JsonType',
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


def test_recursive_type_alias_name():
    T = TypeVar('T')

    @dataclass
    class MyGeneric(Generic[T]):
        field: T

    MyRecursiveType = TypeAliasType('MyRecursiveType', Union[MyGeneric['MyRecursiveType'], int])
    json_schema = TypeAdapter(MyRecursiveType).json_schema()
    assert sorted(json_schema['$defs'].keys()) == ['MyGeneric_MyRecursiveType_', 'MyRecursiveType']


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
            {'$ref': '#/$defs/MyList_int__MaxLen_max_length_1_'},
            {'$ref': '#/$defs/MyList_int__MaxLen_max_length_1_'},
        ],
        'maxItems': 2,
        '$defs': {'MyList_int__MaxLen_max_length_1_': {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 1}},
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
        '$ref': '#/$defs/RecursiveGenericAlias_int_',
        '$defs': {
            'RecursiveGenericAlias_int_': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias_int_'}, {'type': 'integer'}]},
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
        'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias_int_'}, {'type': 'integer'}]},
        'maxItems': 1,
        '$defs': {
            'RecursiveGenericAlias_int_': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias_int_'}, {'type': 'integer'}]},
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
            {'$ref': '#/$defs/RecursiveGenericAlias_int__MaxLen_max_length_1_'},
            {'$ref': '#/$defs/RecursiveGenericAlias_int__MaxLen_max_length_1_'},
        ],
        'maxItems': 2,
        '$defs': {
            'RecursiveGenericAlias_int_': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias_int_'}, {'type': 'integer'}]},
            },
            'RecursiveGenericAlias_int__MaxLen_max_length_1_': {
                'type': 'array',
                'items': {'anyOf': [{'$ref': '#/$defs/RecursiveGenericAlias_int_'}, {'type': 'integer'}]},
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
        '$ref': '#/$defs/SomeAlias',
        'title': 'abc',
    }


def test_nested_generic_type_alias_type() -> None:
    class MyModel(BaseModel):
        field_1: MyList[bool]
        field_2: MyList[str]

    model = MyModel(field_1=[True], field_2=['abc'])

    assert model.model_json_schema() == {
        '$defs': {
            'MyList_bool_': {'items': {'type': 'boolean'}, 'type': 'array'},
            'MyList_str_': {'items': {'type': 'string'}, 'type': 'array'},
        },
        'properties': {'field_1': {'$ref': '#/$defs/MyList_bool_'}, 'field_2': {'$ref': '#/$defs/MyList_str_'}},
        'required': ['field_1', 'field_2'],
        'title': 'MyModel',
        'type': 'object',
    }


def test_non_specified_generic_type_alias_type() -> None:
    assert TypeAdapter(MyList).json_schema() == {'items': {}, 'type': 'array'}


def test_redefined_type_alias():
    MyType = TypeAliasType('MyType', str)

    class MyInnerModel(BaseModel):
        x: MyType

    MyType = TypeAliasType('MyType', int)

    class MyOuterModel(BaseModel):
        inner: MyInnerModel
        y: MyType

    data = {'inner': {'x': 'hello'}, 'y': 1}
    assert MyOuterModel.model_validate(data).model_dump() == data


def test_type_alias_to_type_with_ref():
    class Div(BaseModel):
        type: Literal['Div'] = 'Div'
        components: List['AnyComponent']

    AnyComponent = TypeAliasType('AnyComponent', Div)

    adapter = TypeAdapter(AnyComponent)
    adapter.validate_python({'type': 'Div', 'components': [{'type': 'Div', 'components': []}]})
    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_python({'type': 'Div', 'components': [{'type': 'NotDiv', 'components': []}]})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'expected': "'Div'"},
            'input': 'NotDiv',
            'loc': ('components', 0, 'type'),
            'msg': "Input should be 'Div'",
            'type': 'literal_error',
        }
    ]


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason='type statement is available from 3.12',
)
@pytest.mark.parametrize(
    'input_value,error',
    [
        ([1], None),
        (2, 'Input should be an instance of Sequence'),
        (['foo'], None),
        ([True], None),
        ([[]], None),
        ([None], None),
        ([[1, '']], None),
        ([{'a': None}], None),
        ([{'a': [{'foo': 'bar'}]}], None),
        # 5 errors:
        # - value.0.str,
        # - value.0.int,
        # - value.0.bool,
        # - value.0.`list[nullable[union[str,int,bool,...,dict[str,...]]]]`,
        # - value.0.`dict[str,...]`.2.[key]
        ([{2: None}], '5 validation errors for MyModel'),
    ],
    ids=repr,
)
def test_type_alias_with_type_statement(create_module, input_value, error):
    module = create_module(
        """
from typing import Sequence
from pydantic import BaseModel

type JSON = str | int | bool | JSONSeq | JSONObj | None | JSONAlias
type JSONObj = dict[str, JSON]
type JSONSeq = list[JSON]
JSONAlias = JSONSeq
type MyJSONAlias = JSON
type JSONs = Sequence[MyJSONAlias]

class MyModel(BaseModel):
    value: JSONs
"""
    )
    if error is not None:
        with pytest.raises(ValidationError, match=error):
            module.MyModel(value=input_value)
    else:
        module.MyModel(value=input_value)


def test_type_alias_with_generics(create_module):
    module = create_module(
        """
from typing import TypeAlias, TypeVar, Sequence
from pydantic import BaseModel

T = TypeVar("T")
MySeq: TypeAlias = Sequence[T]
MyIntSeq = MySeq[int]

class MyModel(BaseModel):
    v: MyIntSeq
"""
    )
    assert module.MyModel(v=[1]).model_dump() == {'v': [1]}
    with pytest.raises(ValidationError) as exc_info:
        module.MyModel(v=['a'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (
                'v',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
    ]


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason='type statement is available from 3.12',
)
def test_generics_with_type_statement(create_module):
    # essentially test case `test_type_alias_with_generics` with the new syntax
    module = create_module(
        """
from pydantic import BaseModel
from typing import Sequence

type MySeq[T] = Sequence[T]
type MyIntSeq = MySeq[int]

class MyModel(BaseModel):
    v: MyIntSeq
"""
    )
    assert module.MyModel(v=[1]).model_dump() == {'v': [1]}
    with pytest.raises(ValidationError) as exc_info:
        module.MyModel(v=['a'])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (
                'v',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
    ]


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason='type statement is available from 3.12',
)
def test_circular_type_aliasing_with_type_statement(create_module):
    with pytest.raises(PydanticSchemaGenerationError, match='Circular type aliasing detected'):
        create_module(
            """
from pydantic import BaseModel

type A = B
type B = A

class MyModel(BaseModel):
    value: A
"""
        )


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason='type statement is available from 3.12',
)
def test_cyclic_type_aliasing_with_type_statement(create_module):
    module = create_module(
        """
from pydantic import BaseModel
from typing import Union

type A = C
type B = C
type C = Union[A, B]

class MyModel(BaseModel):
    value: C
"""
    )

    with pytest.raises(ValidationError, match='recursion_loop'):
        module.MyModel(value=1)


def test_different_ways_of_type_aliasing(create_module):
    module = create_module(
        """
from typing import NewType, List
from typing_extensions import TypeAlias, TypeAliasType
from pydantic import BaseModel

T1: TypeAlias = List[int]
T2 = TypeAliasType('T2', int)
T3 = List[str]
T4 = NewType('T4', str)

class MyModel(BaseModel):
    a: T1
    b: T2
    c: T3
    d: T4
"""
    )
    assert module.MyModel(a=[1], b=2, c=['foo'], d='bar').model_dump() == {'a': [1], 'b': 2, 'c': ['foo'], 'd': 'bar'}
    with pytest.raises(ValidationError) as exc_info:
        module.MyModel(a='?', b='?', c=[True], d=2)
    assert sorted(exc_info.value.errors(include_url=False), key=lambda x: x['loc']) == [
        {
            'type': 'list_type',
            'loc': ('a',),
            'msg': 'Input should be a valid list',
            'input': '?',
        },
        {
            'type': 'int_parsing',
            'loc': ('b',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': '?',
        },
        {
            'type': 'string_type',
            'loc': (
                'c',
                0,
            ),
            'msg': 'Input should be a valid string',
            'input': True,
        },
        {
            'type': 'string_type',
            'loc': ('d',),
            'msg': 'Input should be a valid string',
            'input': 2,
        },
    ]


def test_different_ways_of_type_aliasing_nested(create_module):
    module = create_module(
        """
from typing import NewType, List
from typing_extensions import TypeAlias, TypeAliasType
from pydantic import BaseModel

T1: TypeAlias = List[int]
T2 = TypeAliasType('T2', T1)
T3 = T2
T4 = NewType('T4', T3)

class MyModel(BaseModel):
    a: T1
    b: T2
    c: T3
    d: T4
"""
    )
    assert module.MyModel(a=[1], b=[1], c=[1], d=[1]).model_dump() == {'a': [1], 'b': [1], 'c': [1], 'd': [1]}
    with pytest.raises(ValidationError) as exc_info:
        module.MyModel(a=['a'], b=['a'], c=['a'], d=['a'])
    assert sorted(exc_info.value.errors(include_url=False), key=lambda x: x['loc']) == [
        {
            'type': 'int_parsing',
            'loc': (
                'a',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (
                'b',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (
                'c',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (
                'd',
                0,
            ),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
    ]
