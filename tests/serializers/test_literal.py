from dataclasses import dataclass
from enum import Enum
from typing import Literal, Union

import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema

from ..conftest import plain_repr


def test_int_literal():
    s = SchemaSerializer(core_schema.literal_schema([1, 2, 3]))
    r = plain_repr(s)
    assert 'expected_int:{' in r
    assert 'expected_str:{}' in r
    assert 'expected_py:None' in r

    assert s.to_python(1) == 1
    assert s.to_python(1, mode='json') == 1
    assert s.to_python(44) == 44
    assert s.to_json(1) == b'1'

    # with pytest.warns(UserWarning, match='Expected `int` but got `str` - serialized value may not be as expected'):
    assert s.to_python('a', mode='json') == 'a'

    # with pytest.warns(UserWarning, match='Expected `int` but got `str` - serialized value may not be as expected'):
    assert s.to_json('a') == b'"a"'


def test_str_literal():
    s = SchemaSerializer(core_schema.literal_schema(['a', 'b', 'c']))
    r = plain_repr(s)
    assert 'expected_str:{' in r
    assert 'expected_int:{}' in r
    assert 'expected_py:None' in r

    assert s.to_python('a') == 'a'
    assert s.to_python('a', mode='json') == 'a'
    assert s.to_python('not in literal') == 'not in literal'
    assert s.to_json('a') == b'"a"'

    # with pytest.warns(UserWarning, match='Expected `str` but got `int` - serialized value may not be as expected'):
    assert s.to_python(1, mode='json') == 1

    # with pytest.warns(UserWarning, match='Expected `str` but got `int` - serialized value may not be as expected'):
    assert s.to_json(1) == b'1'


def test_other_literal():
    s = SchemaSerializer(core_schema.literal_schema(['a', 1]))
    assert 'expected_int:{1},expected_str:{"a"},expected_py:None' in plain_repr(s)

    assert s.to_python('a') == 'a'
    assert s.to_python('a', mode='json') == 'a'
    assert s.to_python('not in literal') == 'not in literal'
    assert s.to_json('a') == b'"a"'

    assert s.to_python(1) == 1
    assert s.to_python(1, mode='json') == 1
    assert s.to_python(44) == 44
    assert s.to_json(1) == b'1'


def test_empty_literal():
    with pytest.raises(SchemaError, match='`expected` should have length > 0'):
        SchemaSerializer(core_schema.literal_schema([]))


def test_bool_literal():
    s = SchemaSerializer(core_schema.literal_schema([False]))
    assert 'expected_int:{},expected_str:{},expected_py:Some(Py(' in plain_repr(s)

    assert s.to_python(False) is False
    assert s.to_python(False, mode='json') is False
    assert s.to_python(True) is True
    assert s.to_json(False) == b'false'


def test_literal_with_enum() -> None:
    class SomeEnum(str, Enum):
        CAT = 'cat'
        DOG = 'dog'

    @dataclass
    class Dog:
        name: str
        type: Literal[SomeEnum.DOG] = SomeEnum.DOG

    @dataclass
    class Cat:
        name: str
        type: Literal[SomeEnum.CAT] = SomeEnum.CAT

    @dataclass
    class Yard:
        pet: Union[Dog, Cat]

    serializer = SchemaSerializer(
        core_schema.model_schema(
            cls=Yard,
            schema=core_schema.model_fields_schema(
                fields={
                    'pet': core_schema.model_field(
                        schema=core_schema.tagged_union_schema(
                            choices={
                                SomeEnum.DOG: core_schema.model_schema(
                                    cls=Dog,
                                    schema=core_schema.model_fields_schema(
                                        fields={
                                            'type': core_schema.model_field(
                                                schema=core_schema.with_default_schema(
                                                    schema=core_schema.literal_schema([SomeEnum.DOG]),
                                                    default=SomeEnum.DOG,
                                                )
                                            ),
                                            'name': core_schema.model_field(schema=core_schema.str_schema()),
                                        },
                                        model_name='Dog',
                                    ),
                                ),
                                SomeEnum.CAT: core_schema.model_schema(
                                    cls=Cat,
                                    schema=core_schema.model_fields_schema(
                                        fields={
                                            'type': core_schema.model_field(
                                                schema=core_schema.with_default_schema(
                                                    schema=core_schema.literal_schema([SomeEnum.CAT]),
                                                    default=SomeEnum.CAT,
                                                )
                                            ),
                                            'name': core_schema.model_field(schema=core_schema.str_schema()),
                                        },
                                        model_name='Cat',
                                    ),
                                ),
                            },
                            discriminator='type',
                            strict=False,
                            from_attributes=True,
                        )
                    )
                }
            ),
        )
    )

    yard = Yard(pet=Dog(name='Rex'))
    assert serializer.to_python(yard, mode='json') == {'pet': {'type': 'dog', 'name': 'Rex'}}
