from collections import deque
from typing import Annotated, Any

import pytest

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


def test_deque_success() -> None:
    ta = TypeAdapter(deque)

    assert ta.validate_python([1, 2, 3]) == deque([1, 2, 3])


@pytest.mark.parametrize(
    'cls,value,result',
    (
        (int, [1, 2, 3], deque([1, 2, 3])),
        (int, (1, 2, 3), deque((1, 2, 3))),
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (float, [1.0, 2.0, 3.0], deque([1.0, 2.0, 3.0])),
        (set[int], [{1, 2}, {3, 4}, {5, 6}], deque([{1, 2}, {3, 4}, {5, 6}])),
        (tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), deque(((1, 'a'), (2, 'b'), (3, 'c')))),
        (str, 'one two three'.split(), deque(['one', 'two', 'three'])),
        (
            int,
            {1: 10, 2: 20, 3: 30}.keys(),
            deque([1, 2, 3]),
        ),
        (
            int,
            {1: 10, 2: 20, 3: 30}.values(),
            deque([10, 20, 30]),
        ),
        (
            tuple[int, int],
            {1: 10, 2: 20, 3: 30}.items(),
            deque([(1, 10), (2, 20), (3, 30)]),
        ),
        (
            float,
            {1, 2, 3},
            deque([1, 2, 3]),
        ),
        (
            float,
            frozenset((1, 2, 3)),
            deque([1, 2, 3]),
        ),
    ),
)
def test_deque_generic_success(cls, value, result) -> None:
    ta = TypeAdapter(deque[cls])

    assert ta.validate_python(value) == result


@pytest.mark.parametrize(
    'cls,value,result',
    (
        (int, deque((1, 2, 3)), deque((1, 2, 3))),
        (str, deque(('1', '2', '3')), deque(('1', '2', '3'))),
    ),
)
def test_deque_generic_success_strict(cls, value: Any, result) -> None:
    ta = TypeAdapter(deque[cls], config=ConfigDict(strict=True))

    assert ta.validate_python(value) == result


@pytest.mark.parametrize(
    'cls,value,expected_error',
    (
        (
            int,
            [1, 'a', 3],
            {
                'type': 'int_parsing',
                'loc': (1,),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            int,
            (1, 2, 'a'),
            {
                'type': 'int_parsing',
                'loc': (2,),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            {
                'type': 'int_parsing',
                'loc': (1, 0),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'a',
            },
        ),
        (
            list[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            {
                'type': 'list_type',
                'loc': (0,),
                'msg': 'Input should be a valid list',
                'input': {
                    'a': 1,
                    'b': 2,
                },
            },
        ),
    ),
)
def test_deque_fails(cls, value, expected_error) -> None:
    ta = TypeAdapter(deque[cls])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    # debug(exc_info.value.errors(include_url=False))
    assert len(exc_info.value.errors(include_url=False)) == 1
    assert expected_error == exc_info.value.errors(include_url=False)[0]


def test_deque_model() -> None:
    class Model2(BaseModel):
        x: int

    ta = TypeAdapter(deque[Model2])

    seq = [Model2(x=1), Model2(x=2)]
    assert ta.validate_python(seq) == deque(seq)


def test_deque_json() -> None:
    ta = TypeAdapter(deque[int])

    assert ta.dump_json(ta.validate_python((1, 2, 3))) == b'[1,2,3]'


def test_deque_any_maxlen() -> None:
    class DequeModel1(BaseModel):
        field: deque

    assert DequeModel1(field=deque()).field.maxlen is None
    assert DequeModel1(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel2(BaseModel):
        field: deque = deque()

    assert DequeModel2().field.maxlen is None
    assert DequeModel2(field=deque()).field.maxlen is None
    assert DequeModel2(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel3(BaseModel):
        field: deque = deque(maxlen=5)

    assert DequeModel3().field.maxlen == 5
    assert DequeModel3(field=deque()).field.maxlen is None
    assert DequeModel3(field=deque(maxlen=8)).field.maxlen == 8


def test_deque_typed_maxlen() -> None:
    class DequeModel1(BaseModel):
        field: deque[int]

    assert DequeModel1(field=deque()).field.maxlen is None
    assert DequeModel1(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel2(BaseModel):
        field: deque[int] = deque()

    assert DequeModel2().field.maxlen is None
    assert DequeModel2(field=deque()).field.maxlen is None
    assert DequeModel2(field=deque(maxlen=8)).field.maxlen == 8

    class DequeModel3(BaseModel):
        field: deque[int] = deque(maxlen=5)

    assert DequeModel3().field.maxlen == 5
    assert DequeModel3(field=deque()).field.maxlen is None
    assert DequeModel3(field=deque(maxlen=8)).field.maxlen == 8


def test_deque_enforces_maxlen() -> None:
    ta = TypeAdapter(Annotated[deque[int], Field(max_length=3)])

    with pytest.raises(ValidationError):
        ta.validate_python(deque([1, 2, 3, 4]))


def test_deque_strict_fails() -> None:
    ta = TypeAdapter(deque[int], config=ConfigDict(strict=True))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'deque_type', 'loc': (), 'msg': 'Input should be a valid deque', 'input': [1, 2]}
    ]

    # JSON arrays are always accepted:
    assert ta.validate_json('[1, 2]') == deque([1, 2])


def test_deque_constraints_core_schema() -> None:
    ta = TypeAdapter(Annotated[deque[int], Field(min_length=1, max_length=3, fail_fast=True)])

    with pytest.raises(ValidationError, match='Deque should have at least 1 item after validation, not 0'):
        ta.validate_python([])
    with pytest.raises(ValidationError, match='Deque should have at most 3 items after validation, not 4'):
        ta.validate_python(deque([1, 2, 3, 4]))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 'a', 'b'])
    assert len(exc_info.value.errors()) == 1


def test_deque_constraints_json_schema() -> None:
    ta = TypeAdapter(Annotated[deque[int], Field(min_length=1, max_length=3)])

    assert ta.json_schema() == {'type': 'array', 'items': {'type': 'integer'}, 'minItems': 1, 'maxItems': 3}


def test_deque_maxlen_preserved_with_constraints() -> None:
    ta = TypeAdapter(Annotated[deque[int], Field(max_length=3)])

    assert ta.validate_python(deque([1, 2], maxlen=5)).maxlen == 5
    assert ta.validate_python([1, 2]).maxlen is None


def test_deque_serialization() -> None:
    ta = TypeAdapter(deque[int])

    dq = deque([1, 2, 3], maxlen=5)
    assert ta.dump_python(dq) == dq
    assert ta.dump_python(dq).maxlen == 5
    assert ta.dump_python(dq) is not dq
    assert ta.dump_python(dq, mode='json') == [1, 2, 3]
    assert ta.dump_json(dq) == b'[1,2,3]'

    with pytest.warns(UserWarning, match=r'Expected `deque\[int\]` - serialized value may not be as expected'):
        assert ta.dump_python([1, 2, 3]) == [1, 2, 3]
