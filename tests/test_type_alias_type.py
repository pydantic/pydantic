import datetime
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Generic, Literal, TypeVar, Union

import pytest
from annotated_types import MaxLen
from typing_extensions import TypeAliasType

from pydantic import BaseModel, Field, PydanticUserError, TypeAdapter, ValidationError

T = TypeVar('T')

JsonType = TypeAliasType('JsonType', Union[list['JsonType'], dict[str, 'JsonType'], str, int, float, bool, None])
RecursiveGenericAlias = TypeAliasType(
    'RecursiveGenericAlias', list[Union['RecursiveGenericAlias[T]', T]], type_params=(T,)
)
MyList = TypeAliasType('MyList', list[T], type_params=(T,))
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
    t = TypeAdapter(tuple[ShortMyList[int], ShortMyList[int]])

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
    t = TypeAdapter(tuple[ShortRecursiveGenericAlias[int], ShortRecursiveGenericAlias[int]])

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


def test_nested_generic_type_alias_type() -> None:
    class MyModel(BaseModel):
        field_1: MyList[bool]
        field_2: MyList[str]

    MyModel(field_1=[True], field_2=['abc'])

    assert MyModel.model_json_schema() == {
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
        components: list['AnyComponent']

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


def test_intermediate_type_aliases() -> None:
    # https://github.com/pydantic/pydantic/issues/8984
    MySeq = TypeAliasType('MySeq', Sequence[T], type_params=(T,))
    MyIntSeq = TypeAliasType('MyIntSeq', MySeq[int])

    class MyModel(BaseModel):
        my_int_seq: MyIntSeq

    assert MyModel(my_int_seq=range(1, 4)).my_int_seq == [1, 2, 3]

    assert MyModel.model_json_schema() == {
        '$defs': {'MyIntSeq': {'items': {'type': 'integer'}, 'type': 'array'}},
        'properties': {'my_int_seq': {'$ref': '#/$defs/MyIntSeq'}},
        'required': ['my_int_seq'],
        'title': 'MyModel',
        'type': 'object',
    }


def test_intermediate_type_aliases_json_type() -> None:
    JSON = TypeAliasType('JSON', Union[str, int, bool, 'JSONSeq', 'JSONObj', None])
    JSONObj = TypeAliasType('JSONObj', dict[str, JSON])
    JSONSeq = TypeAliasType('JSONSeq', list[JSON])
    MyJSONAlias1 = TypeAliasType('MyJSONAlias1', JSON)
    MyJSONAlias2 = TypeAliasType('MyJSONAlias2', MyJSONAlias1)
    JSONs = TypeAliasType('JSONs', list[MyJSONAlias2])

    adapter = TypeAdapter(JSONs)

    assert adapter.validate_python([{'a': 1}, 2, '3', [4, 5], True, None]) == [{'a': 1}, 2, '3', [4, 5], True, None]


def test_intermediate_type_aliases_chain() -> None:
    A = TypeAliasType('A', int)
    B = TypeAliasType('B', A)
    C = TypeAliasType('C', B)
    D = TypeAliasType('D', C)
    E = TypeAliasType('E', D)

    TypeAdapter(E)


def test_circular_type_aliases() -> None:
    A = TypeAliasType('A', 'C')
    B = TypeAliasType('B', A)
    C = TypeAliasType('C', B)

    with pytest.raises(PydanticUserError) as exc_info:

        class MyModel(BaseModel):
            a: C

    assert exc_info.value.code == 'circular-reference-schema'
    assert exc_info.value.message.startswith('tests.test_type_alias_type.C')


## Tests related to (recursive) unpacking of annotated types, when PEP 695 type aliases are involved:


def test_nested_annotated_with_type_aliases() -> None:
    SomeAlias = TypeAliasType('SomeAlias', Annotated[int, Field(description='number')])

    ta = TypeAdapter(Annotated[SomeAlias, Field(title='abc')])

    assert ta.json_schema() == {'description': 'number', 'title': 'abc', 'type': 'integer'}


@pytest.mark.xfail(
    reason="When trying to recursively unpack the annotated form, we don't resolve "
    'forward annotations in PEP 695 type aliases (due to current limitations) '
    '(see https://github.com/pydantic/pydantic/issues/11122).',
)
def test_nested_annotated_with_type_aliases_and_forward_ref() -> None:
    SomeAlias = TypeAliasType('SomeAlias', "Annotated[int, Field(description='number')]")

    ta = TypeAdapter(Annotated[SomeAlias, Field(title='abc')])

    assert ta.json_schema() == {'description': 'number', 'title': 'abc', 'type': 'integer'}


def test_nested_annotated_model_field() -> None:
    T = TypeVar('T')

    InnerList = TypeAliasType('InnerList', Annotated[list[T], Field(alias='alias')], type_params=(T,))
    MyList = TypeAliasType('MyList', Annotated[InnerList[T], Field(deprecated=True)], type_params=(T,))
    MyIntList = TypeAliasType('MyIntList', MyList[int])

    class Model(BaseModel):
        f1: Annotated[MyIntList, Field(json_schema_extra={'extra': 'test'})]

    f1_info = Model.model_fields['f1']

    assert f1_info.annotation == list[int]
    assert f1_info.alias == 'alias'
    assert f1_info.deprecated
    assert f1_info.json_schema_extra == {'extra': 'test'}
