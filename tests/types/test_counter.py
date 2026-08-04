from collections import Counter

import pytest

from pydantic import BaseModel, ValidationError


def test_typing_coercion_counter():
    class Model(BaseModel):
        x: Counter[str]

    m = Model(x={'a': 10})
    assert isinstance(m.x, Counter)
    assert repr(m.x) == "Counter({'a': 10})"


def test_typing_counter_value_validation():
    class Model(BaseModel):
        x: Counter[str]

    with pytest.raises(ValidationError) as exc_info:
        Model(x={'a': 'a'})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('x', 'a'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]
