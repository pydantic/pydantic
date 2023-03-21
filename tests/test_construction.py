import pickle
from typing import Any, List, Optional

import pytest

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from pydantic.fields import Undefined


class Model(BaseModel):
    a: float
    b: int = 10


def test_simple_construct():
    m = Model.model_construct(a=3.14)
    assert m.a == 3.14
    assert m.b == 10
    assert m.__fields_set__ == {'a'}
    assert m.model_dump() == {'a': 3.14, 'b': 10}


def test_construct_misuse():
    m = Model.model_construct(b='foobar')
    assert m.b == 'foobar'
    with pytest.warns(UserWarning, match='Expected `int` but got `str`'):
        assert m.model_dump() == {'b': 'foobar'}
    with pytest.raises(AttributeError, match="'Model' object has no attribute 'a'"):
        print(m.a)


def test_construct_fields_set():
    m = Model.model_construct(a=3.0, b=-1, _fields_set={'a'})
    assert m.a == 3
    assert m.b == -1
    assert m.__fields_set__ == {'a'}
    assert m.model_dump() == {'a': 3, 'b': -1}


def test_construct_allow_extra():
    """model_construct() should allow extra fields"""

    class Foo(BaseModel, extra='allow'):
        x: int

    assert Foo.model_construct(x=1, y=2).model_dump() == {'x': 1, 'y': 2}


def test_construct_keep_order():
    class Foo(BaseModel):
        a: int
        b: int = 42
        c: float

    instance = Foo(a=1, b=321, c=3.14)
    instance_construct = Foo.model_construct(**instance.model_dump())
    assert instance == instance_construct
    assert instance.model_dump() == instance_construct.model_dump()
    assert instance.model_dump_json() == instance_construct.model_dump_json()


def test_large_any_str():
    class Model(BaseModel):
        a: bytes
        b: str

    content_bytes = b'x' * (2**16 + 1)
    content_str = 'x' * (2**16 + 1)
    m = Model(a=content_bytes, b=content_str)
    assert m.a == content_bytes
    assert m.b == content_str


def test_simple_copy():
    m = Model(a=24)
    m2 = m.copy()

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m == m2
    assert m.model_fields == m2.model_fields


@pytest.fixture(scope='session', name='ModelTwo')
def model_two_fixture():
    class ModelTwo(BaseModel):
        _foo_ = PrivateAttr({'private'})

        a: float
        b: int = 10
        c: str = 'foobar'
        d: Model

    return ModelTwo


def test_deep_copy(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m._foo_ = {'new value'}
    m2 = m.copy(deep=True)

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m.c == m2.c == 'foobar'
    assert m.d is not m2.d
    assert m == m2
    assert m.model_fields == m2.model_fields
    assert m._foo_ == m2._foo_
    assert m._foo_ is not m2._foo_


@pytest.mark.xfail(reason='working on V2')
def test_copy_exclude(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(exclude={'b'})

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m2.d.a == 12

    assert hasattr(m2, 'c')
    assert not hasattr(m2, 'b')
    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a', 'c', 'd'}

    assert m != m2


@pytest.mark.xfail(reason='working on V2')
def test_copy_include(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(include={'a'})

    assert m.a == m2.a == 24
    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a'}

    assert m != m2


@pytest.mark.xfail(reason='working on V2')
def test_copy_include_exclude(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(include={'a', 'b', 'c'}, exclude={'c'})

    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a', 'b'}


@pytest.mark.xfail(reason='working on V2')
def test_copy_advanced_exclude():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))
    m2 = m.copy(exclude={'f': {'c': ..., 'd': {-1: {'a'}}}})
    assert hasattr(m.f, 'c')
    assert not hasattr(m2.f, 'c')

    assert m2.model_dump() == {'e': 'e', 'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}}
    m2 = m.copy(exclude={'e': ..., 'f': {'d'}})
    assert m2.model_dump() == {'f': {'c': 'foo'}}


@pytest.mark.xfail(reason='working on V2')
def test_copy_advanced_include():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))
    m2 = m.copy(include={'f': {'c'}})
    assert hasattr(m.f, 'c')
    assert hasattr(m2.f, 'c')
    assert m2.model_dump() == {'f': {'c': 'foo'}}

    m2 = m.copy(include={'e': ..., 'f': {'d': {-1}}})
    assert m2.model_dump() == {'e': 'e', 'f': {'d': [{'a': 'c', 'b': 'e'}]}}


@pytest.mark.xfail(reason='working on V2')
def test_copy_advanced_include_exclude():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))
    m2 = m.copy(include={'e': ..., 'f': {'d'}}, exclude={'e': ..., 'f': {'d': {0}}})
    assert m2.model_dump() == {'f': {'d': [{'a': 'c', 'b': 'e'}]}}


@pytest.mark.xfail(reason='working on V2')
def test_copy_update(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy(update={'a': 'different'})

    assert m.a == 24
    assert m2.a == 'different'
    assert set(m.model_dump().keys()) == set(m2.model_dump().keys()) == {'a', 'b', 'c', 'd'}

    assert m != m2


@pytest.mark.xfail(reason='working on V2')
def test_copy_update_unset():
    class Foo(BaseModel):
        foo: Optional[str]
        bar: Optional[str]

    assert (
        Foo(foo='hello').copy(update={'bar': 'world'}).model_dump_json(exclude_unset=True)
        == '{"foo": "hello", "bar": "world"}'
    )


def test_copy_set_fields(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.copy()

    assert m.model_dump(exclude_unset=True) == {'a': 24.0, 'd': {'a': 12}}
    assert m.model_dump(exclude_unset=True) == m2.model_dump(exclude_unset=True)


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
    assert m.model_fields == m2.model_fields


def test_recursive_pickle(create_module):
    @create_module
    def module():
        from pydantic import BaseModel, PrivateAttr

        class PickleModel(BaseModel):
            a: float
            b: int = 10

        class PickleModelTwo(BaseModel):
            _foo_ = PrivateAttr({'private'})

            a: float
            b: int = 10
            c: str = 'foobar'
            d: PickleModel

    m = module.PickleModelTwo(a=24, d=module.PickleModel(a='123.45'))
    m2 = pickle.loads(pickle.dumps(m))
    assert m == m2

    assert m.d.a == 123.45
    assert m2.d.a == 123.45
    assert m.model_fields == m2.model_fields
    assert m._foo_ == m2._foo_


def test_pickle_undefined(create_module):
    @create_module
    def module():
        from pydantic import BaseModel, PrivateAttr

        class PickleModel(BaseModel):
            a: float
            b: int = 10

        class PickleModelTwo(BaseModel):
            _foo_ = PrivateAttr({'private'})

            a: float
            b: int = 10
            c: str = 'foobar'
            d: PickleModel

    m = module.PickleModelTwo(a=24, d=module.PickleModel(a='123.45'))
    m2 = pickle.loads(pickle.dumps(m))
    assert m2._foo_ == {'private'}

    m._foo_ = Undefined
    m3 = pickle.loads(pickle.dumps(m))
    assert not hasattr(m3, '_foo_')


def test_copy_undefined(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='123.45'))
    m2 = m.copy()
    assert m2._foo_ == {'private'}

    m._foo_ = Undefined
    m3 = m.copy()
    assert not hasattr(m3, '_foo_')


def test_immutable_copy_with_frozen():
    class Model(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int
        b: int

    m = Model(a=40, b=10)
    assert m == m.copy()

    m2 = m.copy(update={'b': 12})
    assert repr(m2) == 'Model(a=40, b=12)'
    with pytest.raises(TypeError):
        m2.b = 13


def test_pickle_fields_set():
    m = Model(a=24)
    assert m.model_dump(exclude_unset=True) == {'a': 24}
    m2 = pickle.loads(pickle.dumps(m))
    assert m2.model_dump(exclude_unset=True) == {'a': 24}


@pytest.mark.xfail(reason='working on V2')
def test_copy_update_exclude():
    class SubModel(BaseModel):
        a: str
        b: str

    class Model(BaseModel):
        c: str
        d: SubModel

    m = Model(c='ex', d=dict(a='ax', b='bx'))
    assert m.model_dump() == {'c': 'ex', 'd': {'a': 'ax', 'b': 'bx'}}
    assert m.copy(exclude={'c'}).model_dump() == {'d': {'a': 'ax', 'b': 'bx'}}
    assert m.copy(exclude={'c'}, update={'c': 42}).model_dump() == {'c': 42, 'd': {'a': 'ax', 'b': 'bx'}}

    assert m._calculate_keys(exclude={'x': ...}, include=None, exclude_unset=False) == {'c', 'd'}
    assert m._calculate_keys(exclude={'x': ...}, include=None, exclude_unset=False, update={'c': 42}) == {'d'}


def test_shallow_copy_modify():
    class X(BaseModel):
        val: int
        deep: Any

    x = X(val=1, deep={'deep_thing': [1, 2]})

    y = x.copy()
    y.val = 2
    y.deep['deep_thing'].append(3)

    assert x.val == 1
    assert y.val == 2
    # deep['deep_thing'] gets modified
    assert x.deep['deep_thing'] == [1, 2, 3]
    assert y.deep['deep_thing'] == [1, 2, 3]


@pytest.mark.xfail(reason='working on V2')
def test_construct_default_factory():
    class Model(BaseModel):
        foo: List[int] = Field(default_factory=list)
        bar: str = 'Baz'

    m = Model.model_construct()
    assert m.foo == []
    assert m.bar == 'Baz'


def test_copy_with_excluded_fields():
    class User(BaseModel):
        name: str
        age: int
        dob: str

    user = User(name='test_user', age=23, dob='01/01/2000')
    user_copy = user.copy(exclude={'dob': ...})

    assert 'dob' in user.__fields_set__
    assert 'dob' not in user_copy.__fields_set__


def test_dunder_copy(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.__copy__()
    assert m is not m2

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m.d is m2.d
    assert m.d.a == m2.d.a == 12

    m.a = 12
    assert m.a != m2.a
