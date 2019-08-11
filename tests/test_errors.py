from typing import Union

import pytest
from typing_extensions import Literal

from pydantic import BaseModel, PydanticTypeError, ValidationError, validator


def test_pydantic_error():
    class TestError(PydanticTypeError):
        code = 'test_code'
        msg_template = 'test message template "{test_ctx}"'

        def __init__(self, *, test_ctx: int) -> None:
            super().__init__(test_ctx=test_ctx)

    with pytest.raises(TestError) as exc_info:
        raise TestError(test_ctx='test_value')
    assert str(exc_info.value) == 'test message template "test_value"'


def test_interval_validation_error():
    class Foo(BaseModel):
        model_type: Literal['foo']
        f: int

    class Bar(BaseModel):
        model_type: Literal['bar']
        b: int

    class MyModel(BaseModel):
        foobar: Union[Foo, Bar]

        @validator('foobar', pre=True, whole=True)
        def check_action(cls, v):
            if isinstance(v, dict):
                model_type = v.get('model_type')
                if model_type == 'foo':
                    return Foo(**v)
                if model_type == 'bar':
                    return Bar(**v)
            raise ValueError('not valid Foo or Bar')

    m1 = MyModel(foobar={'model_type': 'foo', 'f': '1'})
    assert m1.foobar.f == 1
    assert isinstance(m1.foobar, Foo)

    m2 = MyModel(foobar={'model_type': 'bar', 'b': '2'})
    assert m2.foobar.b == 2
    assert isinstance(m2.foobar, BaseModel)

    with pytest.raises(ValidationError) as exc_info:
        MyModel(foobar={'model_type': 'foo', 'f': 'x'})
    assert exc_info.value.errors() == [
        {'loc': ('foobar', 'f'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
