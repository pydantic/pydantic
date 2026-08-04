import json
from typing import Any

import pytest

from pydantic import TypeAdapter, ValidationError


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


def test_dict_validate_json_any_value():
    ta = TypeAdapter(dict[str, Any])

    assert ta.validate_json('{"1": 1, "2": "a", "3": null}') == {'1': 1, '2': 'a', '3': None}
