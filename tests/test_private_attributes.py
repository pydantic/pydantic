from typing import ClassVar, Generic, TypeVar

import pytest

from pydantic import BaseModel, Extra, PrivateAttr
from pydantic.fields import Undefined
from pydantic.generics import GenericModel


def test_private_attribute():
    default = {'a': {}}

    class Model(BaseModel):
        _foo = PrivateAttr(default)

    assert Model.__slots__ == {'_foo'}
    assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"
    assert Model.__private_attributes__ == {'_foo': PrivateAttr(default)}

    m = Model()
    assert m._foo == default
    assert m._foo is not default
    assert m._foo['a'] is not default['a']

    m._foo = None
    assert m._foo is None

    assert m.model_dump() == {}
    assert m.__dict__ == {}


def test_private_attribute_nested():
    class SubModel(BaseModel):
        _foo = PrivateAttr(42)
        x: int

    class Model(BaseModel):
        y: int
        sub: SubModel

    m = Model(y=1, sub={'x': 2})
    assert m.sub._foo == 42


def test_private_attribute_factory():
    default = {'a': {}}

    def factory():
        return default

    class Model(BaseModel):
        _foo = PrivateAttr(default_factory=factory)

    assert Model.__slots__ == {'_foo'}
    assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"
    assert Model.__private_attributes__ == {'_foo': PrivateAttr(default_factory=factory)}

    m = Model()
    assert m._foo == default
    assert m._foo is default
    assert m._foo['a'] is default['a']

    m._foo = None
    assert m._foo is None

    assert m.model_dump() == {}
    assert m.__dict__ == {}


def test_private_attribute_annotation():
    class Model(BaseModel):
        """The best model"""

        _foo: str

        class Config:
            underscore_attrs_are_private = True

    assert Model.__slots__ == {'_foo'}
    assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"
    assert Model.__private_attributes__ == {'_foo': PrivateAttr(Undefined)}
    assert repr(Model.__doc__) == "'The best model'"

    m = Model()
    with pytest.raises(AttributeError):
        m._foo

    m._foo = '123'
    assert m._foo == '123'

    m._foo = None
    assert m._foo is None

    del m._foo

    with pytest.raises(AttributeError):
        m._foo

    m._foo = '123'
    assert m._foo == '123'

    assert m.model_dump() == {}
    assert m.__dict__ == {}


@pytest.mark.xfail(reason='ClassVar needs work')
def test_underscore_attrs_are_private():
    class Model(BaseModel):
        _foo: str = 'abc'
        _bar: ClassVar[str] = 'cba'

        class Config:
            underscore_attrs_are_private = True

    assert Model.__slots__ == {'_foo'}
    assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"
    assert Model._bar == 'cba'
    assert Model.__private_attributes__ == {'_foo': PrivateAttr('abc')}

    m = Model()
    assert m._foo == 'abc'
    m._foo = None
    assert m._foo is None

    with pytest.raises(ValueError, match='"Model" object has no field "_bar"'):
        m._bar = 1


def test_private_attribute_intersection_with_extra_field():
    class Model(BaseModel):
        _foo = PrivateAttr('private_attribute')

        class Config:
            extra = Extra.allow

    assert Model.__slots__ == {'_foo'}
    m = Model(_foo='field')
    assert m._foo == 'private_attribute'
    assert m.__dict__ == m.model_dump() == {'_foo': 'field'}

    m._foo = 'still_private'
    assert m._foo == 'still_private'
    assert m.__dict__ == m.model_dump() == {'_foo': 'field'}


def test_private_attribute_invalid_name():
    with pytest.raises(
        NameError,
        match='Private attributes "foo" must not be a valid field name; Use sunder names, e. g. "_foo"',
    ):

        class Model(BaseModel):
            foo = PrivateAttr()


@pytest.mark.xfail(reason="not sure what's going on here???")
def test_slots_are_ignored():
    class Model(BaseModel):
        __slots__ = (
            'foo',
            '_bar',
        )

        def __init__(self):
            super().__init__()
            for attr_ in self.__slots__:
                object.__setattr__(self, attr_, 'spam')

    assert Model.__private_attributes__ == {}
    assert set(Model.__slots__) == {'foo', '_bar'}
    m = Model()
    for attr in Model.__slots__:
        assert object.__getattribute__(m, attr) == 'spam'
        with pytest.raises(ValueError, match=f'"Model" object has no field "{attr}"'):
            setattr(m, attr, 'not spam')


def test_default_and_default_factory_used_error():
    with pytest.raises(ValueError, match='cannot specify both default and default_factory'):
        PrivateAttr(default=123, default_factory=lambda: 321)


def test_config_override_init():
    class MyModel(BaseModel):
        x: str
        _private_attr: int

        def __init__(self, **data) -> None:
            super().__init__(**data)
            self._private_attr = 123

        class Config:
            underscore_attrs_are_private = True

    m = MyModel(x='hello')
    assert m.model_dump() == {'x': 'hello'}
    assert m._private_attr == 123


@pytest.mark.xfail(reason='generics not implemented')
def test_generic_private_attribute():
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        value: T
        _private_value: T

        class Config:
            underscore_attrs_are_private = True

    m = Model[int](value=1, _private_attr=3)
    m._private_value = 3
    assert m.model_dump() == {'value': 1}


@pytest.mark.xfail(reason='config inheritance error')
def test_private_attribute_multiple_inheritance():
    # We need to test this since PrivateAttr uses __slots__ and that has some restrictions with regards to
    # multiple inheritance
    default = {'a': {}}

    class GrandParentModel(BaseModel):
        _foo = PrivateAttr(default)

    class ParentAModel(GrandParentModel):
        pass

    class ParentBModel(GrandParentModel):
        _bar = PrivateAttr(default)

    class Model(ParentAModel, ParentBModel):
        _baz = PrivateAttr(default)

    assert GrandParentModel.__slots__ == {'_foo'}
    assert ParentBModel.__slots__ == {'_bar'}
    assert Model.__slots__ == {'_baz'}
    assert repr(Model._foo) == "<member '_foo' of 'GrandParentModel' objects>"
    assert repr(Model._bar) == "<member '_bar' of 'ParentBModel' objects>"
    assert repr(Model._baz) == "<member '_baz' of 'Model' objects>"
    assert Model.__private_attributes__ == {
        '_foo': PrivateAttr(default),
        '_bar': PrivateAttr(default),
        '_baz': PrivateAttr(default),
    }

    m = Model()
    assert m._foo == default
    assert m._foo is not default
    assert m._foo['a'] is not default['a']

    assert m._bar == default
    assert m._bar is not default
    assert m._bar['a'] is not default['a']

    assert m._baz == default
    assert m._baz is not default
    assert m._baz['a'] is not default['a']

    m._foo = None
    assert m._foo is None

    m._bar = None
    assert m._bar is None

    m._baz = None
    assert m._baz is None

    assert m.model_dump() == {}
    assert m.__dict__ == {}
