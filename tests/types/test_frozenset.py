from collections import deque
from typing import Annotated

import annotated_types
import pytest

from pydantic import BaseModel, ConfigDict, Field, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (frozenset(['1', '2']), frozenset(['1', '2'])),
        (['1', '2', '1', '2'], frozenset(['1', '2'])),
        (('1', '2', '1', '2'), frozenset(['1', '2'])),
        ({'1', '2'}, frozenset(['1', '2'])),
        ({'1': 1, '2': 2}.keys(), frozenset(['1', '2'])),
        ({'1': '1', '2': '2'}.values(), frozenset(['1', '2'])),
        ({'1': 1, '2': 2}, ValidationError),
    ],
)
def test_frozenset_validation(value, expected):
    class Model(BaseModel):
        v: frozenset[str]

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_confrozenset():
    class Model(BaseModel):
        foo: frozenset[int] = Field(min_length=2, max_length=4)
        bar: Annotated[frozenset[str], annotated_types.Len(1, 4)] = None

    m = Model(foo=[1, 2], bar=['spoon'])
    assert m.model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}
    assert isinstance(m.foo, frozenset)
    assert isinstance(m.bar, frozenset)

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Frozenset should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Frozenset should have at most 4 items after validation, not more'):
        Model(foo=list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('foo', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('foo', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_set_type', 'loc': ('foo',), 'msg': 'Input should be a valid frozenset', 'input': 1}
    ]


def test_confrozenset_not_required():
    class Model(BaseModel):
        foo: frozenset[int] | None = None

    assert Model(foo=None).foo is None
    assert Model().foo is None


def test_constrained_frozenset_optional():
    class Model(BaseModel):
        req: Annotated[frozenset[str], annotated_types.Len(1)] | None
        opt: Annotated[frozenset[str], annotated_types.Len(1)] | None = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=frozenset(), opt=frozenset())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'Frozenset should have at least 1 item after validation, not 0',
            'input': frozenset(),
            'ctx': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'Frozenset should have at least 1 item after validation, not 0',
            'input': frozenset(),
            'ctx': {'field_type': 'Frozenset', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).model_dump() == {'req': {'a'}, 'opt': {'a'}}


def test_frozenset_strict() -> None:
    class LaxModel(BaseModel):
        v: frozenset[int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: frozenset[int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=(1, 2)).v == frozenset((1, 2))
    assert LaxModel(v=('1', 2)).v == frozenset((1, 2))
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=(1, 2))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'frozen_set_type',
            'loc': ('v',),
            'msg': 'Input should be a valid frozenset',
            'input': (1, 2),
        }
    ]
    # Strict in each set item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=frozenset(('1', 2)))
    err_info = exc_info.value.errors(include_url=False)
    # Sets are not ordered
    del err_info[0]['loc']
    assert err_info == [{'type': 'int_type', 'msg': 'Input should be a valid integer', 'input': '1'}]


def test_frozenset_field():
    class FrozenSetModel(BaseModel):
        set: frozenset[int]

    test_set = frozenset({1, 2, 3})
    object_under_test = FrozenSetModel(set=test_set)

    assert object_under_test.set == test_set


@pytest.mark.parametrize(
    'value,result',
    [
        ([1, 2, 3], frozenset([1, 2, 3])),
        ({1, 2, 3}, frozenset([1, 2, 3])),
        ((1, 2, 3), frozenset([1, 2, 3])),
        (deque([1, 2, 3]), frozenset([1, 2, 3])),
    ],
)
def test_frozenset_field_conversion(value, result):
    class FrozenSetModel(BaseModel):
        set: frozenset[int]

    object_under_test = FrozenSetModel(set=value)

    assert object_under_test.set == result


def test_frozenset_field_not_convertible():
    class FrozenSetModel(BaseModel):
        set: frozenset[int]

    with pytest.raises(ValidationError, match=r'frozenset'):
        FrozenSetModel(set=42)
