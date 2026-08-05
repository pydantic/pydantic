from collections import Counter

import pytest

from pydantic import TypeAdapter, ValidationError


def test_typing_coercion_counter():
    ta = TypeAdapter(Counter[str])

    v = ta.validate_python({'a': 10})
    assert isinstance(v, Counter)
    assert v == Counter({'a': 10})


def test_typing_counter_value_validation():
    ta = TypeAdapter(Counter[str])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 'a'})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]
