"""Tests related to deferred evaluation of annotations introduced in Python 3.14 by PEP 649 and 749."""

import sys
from dataclasses import field
from typing import Annotated

import pytest
from annotated_types import MaxLen

from pydantic import BaseModel, Field, ValidationError
from pydantic.dataclasses import dataclass

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14), reason='Requires deferred evaluation of annotations introduced in Python 3.14'
)


def test_deferred_annotations_model() -> None:
    class Model(BaseModel):
        a: Int
        b: Str = 'a'

    Int = int
    Str = str

    inst = Model(a='1', b=b'test')
    assert inst.a == 1
    assert inst.b == 'test'


@pytest.mark.xfail(
    reason=(
        'When rebuilding model fields, we individually re-evaluate all fields (using `_eval_type()`) '
        "and as such we don't benefit from PEP 649's capabilities."
    ),
)
def test_deferred_annotations_nested_model() -> None:
    def outer():
        def inner():
            class Model(BaseModel):
                ann: Annotated[List[Dict[str, str]], MaxLen(1)]

            Dict = dict

            return Model

        List = list

        Model = inner()

        return Model

    Model = outer()

    with pytest.raises(ValidationError) as exc_info:
        Model(ann=[{'a': 'b'}, {'c': 'd'}])

    assert exc_info.value.errors()[0]['type'] == 'too_long'


def test_deferred_annotations_pydantic_dataclass() -> None:
    @dataclass
    class A:
        a: Int = field(default=1)

    Int = int

    assert A(a='1').a == 1


def test_deferred_annotations_pydantic_dataclass_pydantic_field() -> None:
    """When initial support for Python 3.14 was added, this failed as support for the Pydantic
    `Field()` function was implemented by writing directly to `__annotations__`.
    """

    @dataclass
    class A:
        a: Int = Field(default=1)

    Int = int

    assert A(a='1').a == 1
