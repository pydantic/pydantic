import pytest

import pydantic
from pydantic import ValidationError


def test_validate_long_string_error():
    class Config:
        max_anystr_length = 3

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    with pytest.raises(ValidationError) as exc_info:
        MyDataclass('xxxx')

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value has at most 3 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 3},
        }
    ]


def test_validate_assigment_long_string_error():
    class Config:
        max_anystr_length = 3
        validate_assignment = True

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    d = MyDataclass('xxx')
    with pytest.raises(ValidationError) as exc_info:
        d.a = 'xxxx'

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value has at most 3 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 3},
        }
    ]


def test_no_validate_assigment_long_string_error():
    class Config:
        max_anystr_length = 3
        validate_assignment = False

    @pydantic.dataclasses.dataclass(config=Config)
    class MyDataclass:
        a: str

    d = MyDataclass('xxx')
    d.a = 'xxxx'

    assert d.a == 'xxxx'
