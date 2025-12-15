"""Tests related to deferred evaluation of annotations introduced in Python 3.14 by PEP 649 and 749."""

import functools
import sys
from dataclasses import field
from typing import Annotated

import pytest
from annotated_types import MaxLen

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
    validate_call,
)
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


def test_deferred_annotations_return_values() -> None:
    class Model(BaseModel):
        a: int

        @model_validator(mode='after')
        def check(self) -> Model:
            return self

        @model_validator(mode='before')
        def before(cls, data) -> MyDict:
            return data

        @model_serializer(mode='plain')
        def ser(self) -> MyDict:
            return {'a': self.a}

        @field_validator('a', mode='before')
        def validate_a(cls, v) -> MyInt:
            return v

        @field_serializer('a', mode='plain')
        def serialize_a(self, v) -> MyInt:
            return v

    MyDict = dict
    MyInt = int


def test_deferred_annotations_pydantic_extra() -> None:
    """https://github.com/pydantic/pydantic/issues/12393"""

    class Foo(BaseModel, extra='allow'):
        a: MyInt

        __pydantic_extra__: MyDict[str, int]

    MyInt = int
    MyDict = dict

    f = Foo(a='1', extra='1')

    assert f.a == 1
    assert f.extra == 1


def test_deferred_annotations_validate_call_wrapped_function() -> None:
    """https://github.com/pydantic/pydantic/issues/12620

    In Python 3.14, `functools.update_wrapper` copies `__annotate__` instead of
    `__annotations__`. This test ensures that `validate_call` works with wrapped
    functions (e.g. those decorated with `sync_to_async` or similar).
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @validate_call
    @decorator
    def foo(a: int, b: str) -> float:
        return float(a)

    assert foo('1', b'test') == 1.0
