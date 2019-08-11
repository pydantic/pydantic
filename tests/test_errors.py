from typing import Optional, Union

import pytest

from pydantic import BaseModel, PydanticTypeError, ValidationError, validator

try:
    from typing_extensions import Literal
except ImportError:
    Literal = None


def test_pydantic_error():
    class TestError(PydanticTypeError):
        code = 'test_code'
        msg_template = 'test message template "{test_ctx}"'

        def __init__(self, *, test_ctx: int) -> None:
            super().__init__(test_ctx=test_ctx)

    with pytest.raises(TestError) as exc_info:
        raise TestError(test_ctx='test_value')
    assert str(exc_info.value) == 'test message template "test_value"'


@pytest.mark.skipif(not Literal, reason='typing_extensions not installed')
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


def test_error_on_optional():
    class Foobar(BaseModel):
        foo: Optional[str] = None

        @validator('foo', always=True, whole=True)
        def check_foo(cls, v):
            raise ValueError('custom error')

    with pytest.raises(ValidationError) as exc_info:
        Foobar(foo='x')
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'custom error', 'type': 'value_error'}]
    assert repr(exc_info.value.raw_errors[0]) == (
        "<ErrorWrapper {'loc': ('foo',), 'msg': 'custom error', 'type': 'value_error'}>"
    )

    with pytest.raises(ValidationError) as exc_info:
        Foobar(foo=None)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'custom error', 'type': 'value_error'}]
