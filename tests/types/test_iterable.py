import itertools
import re
from collections.abc import Iterable
from typing import Any

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PydanticSchemaGenerationError,
    ValidationError,
    field_validator,
)


def int_iterable():
    i = 0
    while True:
        i += 1
        yield str(i)


def str_iterable():
    while True:
        yield from 'foobarbaz'


def test_infinite_iterable_int():
    class Model(BaseModel):
        it: Iterable[int]

    m = Model(it=int_iterable())

    assert repr(m.it) == 'ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))'

    output = []
    for i in m.it:
        output.append(i)
        if i == 10:
            break

    assert output == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    m = Model(it=[1, 2, 3])
    assert list(m.it) == [1, 2, 3]

    m = Model(it=str_iterable())
    with pytest.raises(ValidationError) as exc_info:
        next(m.it)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'f',
        }
    ]


@pytest.mark.parametrize(
    'type_annotation', (pytest.param(Iterable[Any], id='Iterable[Any]'), pytest.param(Iterable, id='Iterable'))
)
def test_iterable_any(type_annotation):
    class Model(BaseModel):
        it: type_annotation

    m = Model(it=int_iterable())

    output = []
    for i in m.it:
        output.append(i)
        if int(i) == 10:
            break

    assert output == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

    m = Model(it=[1, '2', b'three'])
    assert list(m.it) == [1, '2', b'three']

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]

    class MaxLenModel(BaseModel):
        it: type_annotation = Field(max_length=2)

    m = MaxLenModel(it=[1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        list(m.it)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'Generator should have at most 2 items after validation, not more',
            'input': [1, 2, 3],
            'ctx': {'field_type': 'Generator', 'max_length': 2, 'actual_length': None},
        }
    ]


def test_invalid_iterable():
    class Model(BaseModel):
        it: Iterable[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': ('it',), 'msg': 'Input should be iterable', 'input': 3}
    ]


@pytest.mark.parametrize(
    'config,input_str',
    (
        ({}, 'type=iterable_type, input_value=5, input_type=int'),
        ({'hide_input_in_errors': False}, 'type=iterable_type, input_value=5, input_type=int'),
        ({'hide_input_in_errors': True}, 'type=iterable_type'),
    ),
)
def test_iterable_error_hide_input(config, input_str):
    class Model(BaseModel):
        it: Iterable[int]

        model_config = ConfigDict(**config)

    with pytest.raises(ValidationError, match=re.escape(f'Input should be iterable [{input_str}]')):
        Model(it=5)


def test_infinite_iterable_validate_first():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

        @field_validator('it')
        @classmethod
        def infinite_first_int(cls, it):
            return itertools.chain([next(it)], it)

    m = Model(it=int_iterable(), b=3)

    assert m.b == 3
    assert m.it

    for i in m.it:
        assert i
        if i == 10:
            break

    with pytest.raises(ValidationError) as exc_info:
        Model(it=str_iterable(), b=3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('it', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'f',
        }
    ]


def test_iterable_arbitrary_type():
    class CustomIterable(Iterable):
        def __init__(self, iterable):
            self.iterable = iterable

        def __iter__(self):
            return self

        def __next__(self):
            return next(self.iterable)

    with pytest.raises(
        PydanticSchemaGenerationError,
        match='Unable to generate pydantic-core schema for .*CustomIterable.*. Set `arbitrary_types_allowed=True`',
    ):

        class Model(BaseModel):
            x: CustomIterable
