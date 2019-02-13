import pickle

import pytest

from pydantic import BaseModel


class Model(BaseModel):
    a: float
    b: int = 10


def test_simple_construct():
    m = Model.construct(dict(a=40, b=10), {'a', 'b'})
    assert m.a == 40
    assert m.b == 10


def test_construct_missing():
    m = Model.construct(dict(a='not a float'), {'a'})
    assert m.a == 'not a float'
    with pytest.raises(AttributeError) as exc_info:
        print(m.b)

    assert "'Model' object has no attribute 'b'" in str(exc_info)


def test_large_any_str():
    class Model(BaseModel):
        a: bytes
        b: str

    content_bytes = b"x" * (2 ** 16 + 1)
    content_str = "x" * (2 ** 16 + 1)
    m = Model(a=content_bytes, b=content_str)
    assert m.a == content_bytes
    assert m.b == content_str


def test_simple_copy():
    m = Model(a=24)
    m2 = m.copy()

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m == m2
    assert m.__fields__ == m2.__fields__


class ModelTwo(BaseModel):
    a: float
    b: int = 10
    c: str = 'foobar'
    d: Model


def test_deep_copy():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(deep=True)

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m.c == m2.c == 'foobar'
    assert m.d is not m2.d
    assert m == m2
    assert m.__fields__ == m2.__fields__


def test_copy_exclude():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(exclude={'b'})

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m2.d.a == 12

    assert hasattr(m2, 'c')
    assert not hasattr(m2, 'b')
    assert set(m.dict().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.dict().keys()) == {'a', 'c', 'd'}

    assert m != m2


def test_copy_include():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(include={'a'})

    assert m.a == m2.a == 24
    assert set(m.dict().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.dict().keys()) == {'a'}

    assert m != m2


def test_copy_include_exclude():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(include={'a', 'b', 'c'}, exclude={'c'})

    assert set(m.dict().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.dict().keys()) == {'a', 'b'}


def test_copy_update():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(update={'a': 'different'})

    assert m.a == 24
    assert m2.a == 'different'
    assert set(m.dict().keys()) == set(m2.dict().keys()) == {'a', 'b', 'c', 'd'}

    assert m != m2


def test_copy_set_fields():
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy()

    assert m.dict(skip_defaults=True) == {'a': 24.0, 'd': {'a': 12}}
    assert m.dict(skip_defaults=True) == m2.dict(skip_defaults=True)


def test_simple_pickle():
    m = Model(a='24')
    b = pickle.dumps(m)
    m2 = pickle.loads(b)
    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m == m2
    assert m is not m2
    assert tuple(m) == (('a', 24.0), ('b', 10))
    assert tuple(m2) == (('a', 24.0), ('b', 10))
    assert m.__fields__ == m2.__fields__


def test_recursive_pickle():
    m = ModelTwo(a=24, d=Model(a='123.45'))
    m2 = pickle.loads(pickle.dumps(m))
    assert m == m2

    assert m.d.a == 123.45
    assert m2.d.a == 123.45
    assert m.__fields__ == m2.__fields__


def test_immutable_copy():
    class Model(BaseModel):
        a: int
        b: int

        class Config:
            allow_mutation = False

    m = Model(a=40, b=10)
    assert m == m.copy()

    m2 = m.copy(update={'b': 12})
    assert str(m2) == 'Model a=40 b=12'
    with pytest.raises(TypeError):
        m2.b = 13


def test_pickle_fields_set():
    m = Model(a=24)
    assert m.dict(skip_defaults=True) == {'a': 24}
    m2 = pickle.loads(pickle.dumps(m))
    assert m2.dict(skip_defaults=True) == {'a': 24}
