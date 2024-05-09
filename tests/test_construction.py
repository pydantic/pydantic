import pickle
from typing import Any, List, Optional

import pytest
from pydantic_core import PydanticUndefined, ValidationError

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field, PrivateAttr, PydanticDeprecatedSince20


class Model(BaseModel):
    a: float
    b: int = 10


def test_simple_construct():
    m = Model.model_construct(a=3.14)
    assert m.a == 3.14
    assert m.b == 10
    assert m.model_fields_set == {'a'}
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
    assert m.model_fields_set == {'a'}
    assert m.model_dump() == {'a': 3, 'b': -1}


def test_construct_allow_extra():
    """model_construct() should allow extra fields only in the case of extra='allow'"""

    class Foo(BaseModel, extra='allow'):
        x: int

    model = Foo.model_construct(x=1, y=2)
    assert model.x == 1
    assert model.y == 2


@pytest.mark.parametrize('extra', ['ignore', 'forbid'])
def test_construct_ignore_extra(extra: str) -> None:
    """model_construct() should ignore extra fields only in the case of extra='ignore' or extra='forbid'"""

    class Foo(BaseModel, extra=extra):
        x: int

    model = Foo.model_construct(x=1, y=2)
    assert model.x == 1
    assert model.__pydantic_extra__ is None
    assert 'y' not in model.__dict__


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


def test_construct_with_aliases():
    class MyModel(BaseModel):
        x: int = Field(alias='x_alias')

    my_model = MyModel.model_construct(x_alias=1)
    assert my_model.x == 1
    assert my_model.model_fields_set == {'x'}
    assert my_model.model_dump() == {'x': 1}


def test_construct_with_validation_aliases():
    class MyModel(BaseModel):
        x: int = Field(validation_alias='x_alias')

    my_model = MyModel.model_construct(x_alias=1)
    assert my_model.x == 1
    assert my_model.model_fields_set == {'x'}
    assert my_model.model_dump() == {'x': 1}


def test_large_any_str():
    class Model(BaseModel):
        a: bytes
        b: str

    content_bytes = b'x' * (2**16 + 1)
    content_str = 'x' * (2**16 + 1)
    m = Model(a=content_bytes, b=content_str)
    assert m.a == content_bytes
    assert m.b == content_str


def deprecated_copy(m: BaseModel, *, include=None, exclude=None, update=None, deep=False):
    """
    This should only be used to make calls to the deprecated `copy` method with arguments
    that have been removed from `model_copy`. Otherwise, use the `copy_method` fixture below
    """
    with pytest.warns(
        PydanticDeprecatedSince20,
        match=(
            'The `copy` method is deprecated; use `model_copy` instead. '
            'See the docstring of `BaseModel.copy` for details about how to handle `include` and `exclude`.'
        ),
    ):
        return m.copy(include=include, exclude=exclude, update=update, deep=deep)


@pytest.fixture(params=['copy', 'model_copy'])
def copy_method(request):
    """
    Fixture to test both the old/deprecated `copy` and new `model_copy` methods.
    """
    if request.param == 'copy':
        return deprecated_copy
    else:

        def new_copy_method(m, *, update=None, deep=False):
            return m.model_copy(update=update, deep=deep)

        return new_copy_method


def test_simple_copy(copy_method):
    m = Model(a=24)
    m2 = copy_method(m)

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


def test_deep_copy(ModelTwo, copy_method):
    m = ModelTwo(a=24, d=Model(a='12'))
    m._foo_ = {'new value'}
    m2 = copy_method(m, deep=True)

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m.c == m2.c == 'foobar'
    assert m.d is not m2.d
    assert m == m2
    assert m.model_fields == m2.model_fields
    assert m._foo_ == m2._foo_
    assert m._foo_ is not m2._foo_


def test_copy_exclude(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = deprecated_copy(m, exclude={'b'})

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m2.d.a == 12

    assert hasattr(m2, 'c')
    assert not hasattr(m2, 'b')
    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a', 'c', 'd'}

    assert m != m2


def test_copy_include(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = deprecated_copy(m, include={'a'})

    assert m.a == m2.a == 24
    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a'}

    assert m != m2


def test_copy_include_exclude(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = deprecated_copy(m, include={'a', 'b', 'c'}, exclude={'c'})

    assert set(m.model_dump().keys()) == {'a', 'b', 'c', 'd'}
    assert set(m2.model_dump().keys()) == {'a', 'b'}


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
    m2 = deprecated_copy(m, exclude={'f': {'c': ..., 'd': {-1: {'a'}}}})
    assert hasattr(m.f, 'c')
    assert not hasattr(m2.f, 'c')

    assert m2.model_dump() == {'e': 'e', 'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}}
    m2 = deprecated_copy(m, exclude={'e': ..., 'f': {'d'}})
    assert m2.model_dump() == {'f': {'c': 'foo'}}


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
    m2 = deprecated_copy(m, include={'f': {'c'}})
    assert hasattr(m.f, 'c')
    assert hasattr(m2.f, 'c')
    assert m2.model_dump() == {'f': {'c': 'foo'}}

    m2 = deprecated_copy(m, include={'e': ..., 'f': {'d': {-1}}})
    assert m2.model_dump() == {'e': 'e', 'f': {'d': [{'a': 'c', 'b': 'e'}]}}


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
    m2 = deprecated_copy(m, include={'e': ..., 'f': {'d'}}, exclude={'e': ..., 'f': {'d': {0}}})
    assert m2.model_dump() == {'f': {'d': [{'a': 'c', 'b': 'e'}]}}


def test_copy_update(ModelTwo, copy_method):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = copy_method(m, update={'a': 'different'})

    assert m.a == 24
    assert m2.a == 'different'
    m_keys = m.model_dump().keys()
    with pytest.warns(UserWarning, match='Expected `float` but got `str`'):
        m2_keys = m2.model_dump().keys()
    assert set(m_keys) == set(m2_keys) == {'a', 'b', 'c', 'd'}
    assert m != m2


def test_copy_update_unset(copy_method):
    class Foo(BaseModel):
        foo: Optional[str] = None
        bar: Optional[str] = None

    assert (
        copy_method(Foo(foo='hello'), update={'bar': 'world'}).model_dump_json(exclude_unset=True)
        == '{"foo":"hello","bar":"world"}'
    )


class ExtraModel(BaseModel, extra='allow'):
    pass


def test_copy_deep_extra(copy_method):
    class Foo(BaseModel, extra='allow'):
        pass

    m = Foo(extra=[])
    assert copy_method(m).extra is m.extra
    assert copy_method(m, deep=True).extra == m.extra
    assert copy_method(m, deep=True).extra is not m.extra


def test_copy_set_fields(ModelTwo, copy_method):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = copy_method(m)

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

    m._foo_ = PydanticUndefined
    m3 = pickle.loads(pickle.dumps(m))
    assert not hasattr(m3, '_foo_')


def test_copy_undefined(ModelTwo, copy_method):
    m = ModelTwo(a=24, d=Model(a='123.45'))
    m2 = copy_method(m)
    assert m2._foo_ == {'private'}

    m._foo_ = PydanticUndefined
    m3 = copy_method(m)
    assert not hasattr(m3, '_foo_')


def test_immutable_copy_with_frozen(copy_method):
    class Model(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int
        b: int

    m = Model(a=40, b=10)
    assert m == copy_method(m)
    assert repr(m) == 'Model(a=40, b=10)'

    m2 = copy_method(m, update={'b': 12})
    assert repr(m2) == 'Model(a=40, b=12)'
    with pytest.raises(ValidationError):
        m2.b = 13


def test_pickle_fields_set():
    m = Model(a=24)
    assert m.model_dump(exclude_unset=True) == {'a': 24}
    m2 = pickle.loads(pickle.dumps(m))
    assert m2.model_dump(exclude_unset=True) == {'a': 24}


def test_pickle_preserves_extra():
    m = ExtraModel(a=24)
    assert m.model_extra == {'a': 24}
    m2 = pickle.loads(pickle.dumps(m))
    assert m2.model_extra == {'a': 24}


def test_copy_update_exclude():
    class SubModel(BaseModel):
        a: str
        b: str

    class Model(BaseModel):
        c: str
        d: SubModel

    m = Model(c='ex', d=dict(a='ax', b='bx'))
    assert m.model_dump() == {'c': 'ex', 'd': {'a': 'ax', 'b': 'bx'}}
    assert deprecated_copy(m, exclude={'c'}).model_dump() == {'d': {'a': 'ax', 'b': 'bx'}}
    with pytest.warns(UserWarning, match='Expected `str` but got `int`'):
        assert deprecated_copy(m, exclude={'c'}, update={'c': 42}).model_dump() == {
            'c': 42,
            'd': {'a': 'ax', 'b': 'bx'},
        }

    with pytest.warns(
        PydanticDeprecatedSince20,
        match='The private method `_calculate_keys` will be removed and should no longer be used.',
    ):
        assert m._calculate_keys(exclude={'x': ...}, include=None, exclude_unset=False) == {'c', 'd'}
        assert m._calculate_keys(exclude={'x': ...}, include=None, exclude_unset=False, update={'c': 42}) == {'d'}


def test_shallow_copy_modify(copy_method):
    class X(BaseModel):
        val: int
        deep: Any

    x = X(val=1, deep={'deep_thing': [1, 2]})

    y = copy_method(x)
    y.val = 2
    y.deep['deep_thing'].append(3)

    assert x.val == 1
    assert y.val == 2
    # deep['deep_thing'] gets modified
    assert x.deep['deep_thing'] == [1, 2, 3]
    assert y.deep['deep_thing'] == [1, 2, 3]


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
    user_copy = deprecated_copy(user, exclude={'dob': ...})

    assert 'dob' in user.model_fields_set
    assert 'dob' not in user_copy.model_fields_set


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


def test_dunder_deepcopy(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.__copy__()
    assert m is not m2

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m.d is m2.d
    assert m.d.a == m2.d.a == 12

    m.a = 12
    assert m.a != m2.a


def test_model_copy(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.__copy__()
    assert m is not m2

    assert m.a == m2.a == 24
    assert isinstance(m2.d, Model)
    assert m.d is m2.d
    assert m.d.a == m2.d.a == 12

    m.a = 12
    assert m.a != m2.a


def test_pydantic_extra():
    class Model(BaseModel):
        model_config = dict(extra='allow')
        x: int

    m = Model.model_construct(x=1, y=2)
    assert m.__pydantic_extra__ == {'y': 2}


def test_retain_order_of_fields():
    class MyModel(BaseModel):
        a: str = 'a'
        b: str

    m = MyModel.model_construct(b='b')

    assert m.model_dump_json() == '{"a":"a","b":"b"}'


def test_initialize_with_private_attr():
    class MyModel(BaseModel):
        _a: str

    m = MyModel.model_construct(_a='a')

    assert m._a == 'a'
    assert '_a' in m.__pydantic_private__


def test_model_construct_with_alias_choices() -> None:
    class MyModel(BaseModel):
        a: str = Field(validation_alias=AliasChoices('aaa', 'AAA'))

    assert MyModel.model_construct(a='a_value').a == 'a_value'
    assert MyModel.model_construct(aaa='a_value').a == 'a_value'
    assert MyModel.model_construct(AAA='a_value').a == 'a_value'


def test_model_construct_with_alias_path() -> None:
    class MyModel(BaseModel):
        a: str = Field(validation_alias=AliasPath('aaa', 'AAA'))

    assert MyModel.model_construct(a='a_value').a == 'a_value'
    assert MyModel.model_construct(aaa={'AAA': 'a_value'}).a == 'a_value'


def test_model_construct_with_alias_choices_and_path() -> None:
    class MyModel(BaseModel):
        a: str = Field(validation_alias=AliasChoices('aaa', AliasPath('AAA', 'aaa')))

    assert MyModel.model_construct(a='a_value').a == 'a_value'
    assert MyModel.model_construct(aaa='a_value').a == 'a_value'
    assert MyModel.model_construct(AAA={'aaa': 'a_value'}).a == 'a_value'
