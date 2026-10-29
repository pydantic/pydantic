import json
import sys
from collections import Counter, OrderedDict
from typing import Annotated, Any

import pytest

from pydantic import Field, TypeAdapter, ValidationError


def test_dict():
    ta = TypeAdapter(dict)

    assert ta.validate_python({1: 10, 2: 20}) == {1: 10, 2: 20}
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([(1, 2), (3, 4)])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dict_type',
            'loc': (),
            'msg': 'Input should be a valid dictionary',
            'input': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


def test_dict_validate_json():
    ta = TypeAdapter(dict[int, int])

    assert ta.validate_json('{"1": 2, "3": 4}') == {1: 2, 3: 4}

    # duplicate keys, the last value wins, like with python
    assert json.loads('{"1": 1, "1": 2}') == {'1': 2}
    assert ta.validate_json('{"1": 1, "1": 2}') == {1: 2}


@pytest.mark.parametrize(
    'tp,field_type',
    [
        (dict[int, int], 'Dictionary'),
        (OrderedDict[int, int], 'OrderedDict'),
        (Counter[int], 'Counter'),
        pytest.param(
            'frozendict',
            'Frozendict',
            marks=pytest.mark.skipif(sys.version_info < (3, 15), reason='Requires the `frozendict` builtin type'),
        ),
    ],
)
def test_dict_max_length(tp: Any, field_type: str) -> None:
    if tp == 'frozendict':
        tp = frozendict[int, int]  # noqa: F821
    ta = TypeAdapter(Annotated[tp, Field(max_length=2)])

    # duplicate keys don't count towards the length:
    assert ta.validate_json('{"1": 1, "1": 1, "1": 1, "2": 2}') == {1: 1, 2: 2}
    assert ta.validate_python({'1': 1, '01': 1, 2: 2}) == {1: 1, 2: 2}

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_json('{"1": 1, "2": 2, "3": 3, "4": "invalid"}')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': f'{field_type} should have at most 2 items after validation, not more',
            'input': {'1': 1, '2': 2, '3': 3, '4': 'invalid'},
            'ctx': {'field_type': field_type, 'max_length': 2, 'actual_length': None},
        }
    ]


def test_dict_validate_json_any_value():
    ta = TypeAdapter(dict[str, Any])

    assert ta.validate_json('{"1": 1, "2": "a", "3": null}') == {'1': 1, '2': 'a', '3': None}
