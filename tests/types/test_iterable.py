import itertools
import re
import typing
from collections.abc import Iterable, Iterator
from typing import Annotated, Any

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PydanticSchemaGenerationError,
    TypeAdapter,
    ValidationError,
    field_validator,
    validate_call,
)


def test_infinite_iterable_int():
    def int_iterable():
        i = 0
        while True:
            i += 1
            yield str(i)

    def str_iterable():
        while True:
            yield from 'foobarbaz'

    ta = TypeAdapter(Iterable[int])

    it = ta.validate_python(int_iterable())

    assert repr(it) == 'ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))'

    output = []
    for i in it:
        output.append(i)
        if i == 10:
            break

    assert output == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    assert list(ta.validate_python([1, 2, 3])) == [1, 2, 3]

    it = ta.validate_python(str_iterable())
    with pytest.raises(ValidationError) as exc_info:
        next(it)
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
    def int_iterable():
        i = 0
        while True:
            i += 1
            yield str(i)

    ta = TypeAdapter(type_annotation)

    it = ta.validate_python(int_iterable())

    output = []
    for i in it:
        output.append(i)
        if int(i) == 10:
            break

    assert output == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

    assert list(ta.validate_python([1, '2', b'three'])) == [1, '2', b'three']

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': (), 'msg': 'Input should be iterable', 'input': 3}
    ]

    max_len_ta = TypeAdapter(Annotated[type_annotation, Field(max_length=2)])

    it = max_len_ta.validate_python([1, 2, 3])
    with pytest.raises(ValidationError) as exc_info:
        list(it)
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
    ta = TypeAdapter(Iterable[int])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(3)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'iterable_type', 'loc': (), 'msg': 'Input should be iterable', 'input': 3}
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
    ta = TypeAdapter(Iterable[int], config=ConfigDict(**config))

    with pytest.raises(ValidationError, match=re.escape(f'Input should be iterable [{input_str}]')):
        ta.validate_python(5)


def test_infinite_iterable_validate_first():
    def int_iterable():
        i = 0
        while True:
            i += 1
            yield str(i)

    def str_iterable():
        while True:
            yield from 'foobarbaz'

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
        TypeAdapter(CustomIterable)


@pytest.mark.parametrize(
    'type_annotation',
    (
        pytest.param(Iterator[int], id='Iterator[int]'),
        pytest.param(Iterator[Any], id='Iterator[Any]'),
        pytest.param(Iterator, id='Iterator'),
        pytest.param(typing.Iterator[int], id='typing.Iterator[int]'),
        pytest.param(typing.Iterator, id='typing.Iterator'),
    ),
)
def test_iterator(type_annotation):
    def int_gen():
        yield '1'
        yield 2
        yield 3

    ta = TypeAdapter(type_annotation)
    it = ta.validate_python(int_gen())
    if type_annotation in (Iterator[int], typing.Iterator[int]):
        assert list(it) == [1, 2, 3]
    else:
        assert list(it) == ['1', 2, 3]


def test_iterator_in_model_and_validate_call():
    class StreamModel(BaseModel):
        stream: Iterator[int]

    def gen():
        yield 1
        yield 2

    m = StreamModel(stream=gen())
    assert list(m.stream) == [1, 2]

    @validate_call(validate_return=True)
    def generate_numbers() -> Iterator[int]:
        yield 10
        yield 20

    res = generate_numbers()
    assert list(res) == [10, 20]
