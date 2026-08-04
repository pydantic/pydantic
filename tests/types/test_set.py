import typing
from typing import Annotated

import annotated_types
import pytest

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,result',
    (
        ({1, 2, '3'}, {1, 2, '3'}),
        ((1, 2, 2, '3'), {1, 2, '3'}),
        ([1, 2, 2, '3'], {1, 2, '3'}),
        ({i**2 for i in range(5)}, {0, 1, 4, 9, 16}),
    ),
)
def test_set_success(value, result):
    class Model(BaseModel):
        v: set

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (pytest.param(123, id='int-123'), pytest.param('123', id='str-123')))
def test_set_fails(value):
    class Model(BaseModel):
        v: set

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': value}
    ]


def test_set_type_fails():
    class Model(BaseModel):
        v: set[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': '123'}
    ]


@pytest.mark.parametrize(
    'value,expected',
    [
        ({'1', '2'}, {'1', '2'}),
        (['1', '2', '1', '2'], {'1', '2'}),
        (('1', '2', '1', '2'), {'1', '2'}),
        (frozenset(['1', '2']), {'1', '2'}),
        ({'1': 1, '2': 2}.keys(), {'1', '2'}),
        ({'1': '1', '2': '2'}.values(), {'1', '2'}),
        ({'1': 1, '2': 2}, ValidationError),
    ],
)
def test_set_validation(value, expected):
    class Model(BaseModel):
        v: set[str]

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_constrained_set_good():
    class Model(BaseModel):
        v: set[int] = []

    m = Model(v=[1, 2, 3])
    assert m.v == {1, 2, 3}


def test_constrained_set_default():
    class Model(BaseModel):
        v: set[int] = set()

    m = Model()
    assert m.v == set()


def test_constrained_set_default_invalid():
    class Model(BaseModel):
        v: set[int] = 'not valid, not validated'

    m = Model()
    assert m.v == 'not valid, not validated'


def test_constrained_set_too_long():
    class ConSetModelMax(BaseModel):
        v: Annotated[set[int], annotated_types.Len(0, 10)] = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMax(v={str(i) for i in range(11)})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 10 items after validation, not more',
            'input': {'4', '3', '10', '9', '5', '6', '1', '8', '0', '7', '2'},
            'ctx': {'field_type': 'Set', 'max_length': 10, 'actual_length': None},
        }
    ]


def test_constrained_set_too_short():
    class ConSetModelMin(BaseModel):
        v: Annotated[set[int], annotated_types.Len(1)]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMin(v=[])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_set_optional():
    class Model(BaseModel):
        req: Annotated[set[str], annotated_types.Len(1)] | None
        opt: Annotated[set[str], annotated_types.Len(1)] | None = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=set(), opt=set())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': set(),
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'Set should have at least 1 item after validation, not 0',
            'input': set(),
            'ctx': {'field_type': 'Set', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req={'a'}, opt={'a'}).model_dump() == {'req': {'a'}, 'opt': {'a'}}


def test_constrained_set_constraints():
    class ConSetModelBoth(BaseModel):
        v: Annotated[set[int], annotated_types.Len(7, 11)]

    m = ConSetModelBoth(v=set(range(7)))
    assert m.v == set(range(7))

    m = ConSetModelBoth(v=set(range(11)))
    assert m.v == set(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(6)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('v',),
            'msg': 'Set should have at least 7 items after validation, not 6',
            'input': {0, 1, 2, 3, 4, 5},
            'ctx': {'field_type': 'Set', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(12)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('v',),
            'msg': 'Set should have at most 11 items after validation, not more',
            'input': {0, 8, 1, 9, 2, 10, 3, 7, 11, 4, 6, 5},
            'ctx': {'field_type': 'Set', 'max_length': 11, 'actual_length': None},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'set_type', 'loc': ('v',), 'msg': 'Input should be a valid set', 'input': 1}
    ]


def test_constrained_set_item_type_fails():
    class ConSetModel(BaseModel):
        v: set[int] = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModel(v=['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_constrained_set():
    class Model(BaseModel):
        foo: set[int] = Field(min_length=2, max_length=4)
        bar: Annotated[set[str], annotated_types.Len(1, 4)] = None

    assert Model(foo=[1, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).model_dump() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='Set should have at least 2 items after validation, not 1'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='Set should have at most 4 items after validation, not more'):
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
        {'type': 'set_type', 'loc': ('foo',), 'msg': 'Input should be a valid set', 'input': 1}
    ]


def test_set_not_required():
    class Model(BaseModel):
        foo: set[int] | None = None

    assert Model(foo=None).foo is None
    assert Model().foo is None


def test_set_strict() -> None:
    class LaxModel(BaseModel):
        v: set[int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: set[int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=(1, 2)).v == {1, 2}
    assert LaxModel(v=('1', 2)).v == {1, 2}
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=(1, 2))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'set_type',
            'loc': ('v',),
            'msg': 'Input should be a valid set',
            'input': (1, 2),
        }
    ]
    # Strict in each set item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v={'1', 2})
    err_info = exc_info.value.errors(include_url=False)
    # Sets are not ordered
    del err_info[0]['loc']
    assert err_info == [{'type': 'int_type', 'msg': 'Input should be a valid integer', 'input': '1'}]


def test_typing_mutable_set():
    s1 = TypeAdapter(set[int]).core_schema
    s1.pop('metadata', None)
    s2 = TypeAdapter(typing.MutableSet[int]).core_schema
    s2.pop('metadata', None)
    assert s1 == s2
