import typing
from typing import Literal

import pytest
import typing_extensions

from pydantic import TypeAdapter, ValidationError


def test_literal_single():
    ta = TypeAdapter(Literal['a'])

    assert ta.validate_python('a') == 'a'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('b')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a'",
            'input': 'b',
            'ctx': {'expected': "'a'"},
        }
    ]


def test_literal_multiple():
    ta = TypeAdapter(Literal['a', 'b'])

    assert ta.validate_python('a') == 'a'
    assert ta.validate_python('b') == 'b'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        }
    ]


@pytest.mark.parametrize(
    'typing_literal',
    [
        pytest.param(typing.Literal, id='typing.Literal'),
        pytest.param(typing_extensions.Literal, id='typing_extensions.Literal'),
    ],
)
def test_literal_field(typing_literal):
    ta = TypeAdapter(typing_literal['foo'])

    assert ta.validate_python('foo') == 'foo'
