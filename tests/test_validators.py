from typing import List

import pytest

from pydantic import BaseModel, ValidationError, validator


def test_simple():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    assert Model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')
    assert '"foobar" not found in a' in str(exc_info.value)


def test_validate_whole():
    class Model(BaseModel):
        a: List[int]

        @validator('a', whole=True, pre=True)
        def check_a1(cls, v):
            v.append('123')
            return v

        @validator('a', whole=True)
        def check_a2(cls, v):
            v.append(456)
            return v

    assert Model(a=[1, 2]).a == [1, 2, 123, 456]


def test_validate_kwargs():
    class Model(BaseModel):
        b: int
        a: List[int]

        @validator('a')
        def check_a1(cls, v, values, **kwargs):
            return v + values['b']

    assert Model(a=[1, 2], b=6).a == [7, 8]


def test_validate_whole_error():
    calls = []

    class Model(BaseModel):
        a: List[int]

        @validator('a', whole=True, pre=True)
        def check_a1(cls, v):
            calls.append(f'check_a1 {v}')
            if 1 in v:
                raise ValueError('a1 broken')
            v[0] += 1
            return v

        @validator('a', whole=True)
        def check_a2(cls, v):
            calls.append(f'check_a2 {v}')
            if 10 in v:
                raise ValueError('a2 broken')
            return v

    assert Model(a=[3, 8]).a == [4, 8]
    assert calls == ['check_a1 [3, 8]', 'check_a2 [4, 8]']
    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[1, 3])
    assert 'a1 broken' in str(exc_info.value)
    assert calls == ['check_a1 [1, 3]']

    calls = []
    with pytest.raises(ValidationError) as exc_info:
        Model(a=[5, 10])
    assert 'a2 broken' in str(exc_info.value)
    assert calls == ['check_a1 [5, 10]', 'check_a2 [6, 10]']
