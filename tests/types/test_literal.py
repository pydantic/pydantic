import typing
from typing import Literal

import pytest
import typing_extensions

from pydantic import BaseModel, ValidationError


def test_literal_single():
    class Model(BaseModel):
        a: Literal['a']

    Model(a='a')
    with pytest.raises(ValidationError) as exc_info:
        Model(a='b')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('a',),
            'msg': "Input should be 'a'",
            'input': 'b',
            'ctx': {'expected': "'a'"},
        }
    ]


def test_literal_multiple():
    class Model(BaseModel):
        a_or_b: Literal['a', 'b']

    Model(a_or_b='a')
    Model(a_or_b='b')
    with pytest.raises(ValidationError) as exc_info:
        Model(a_or_b='c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('a_or_b',),
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
    class Model(BaseModel):
        foo: typing_literal['foo']  # noqa: F821

    assert Model(foo='foo').foo == 'foo'
