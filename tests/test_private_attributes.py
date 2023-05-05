import functools
import platform
from typing import ClassVar, Generic, TypeVar

import pytest

from pydantic import BaseModel, ConfigDict, PrivateAttr
from pydantic.fields import Undefined


def test_private_attribute():
    default = {'a': {}}

    class Model(BaseModel):
        _foo = PrivateAttr(default)

    assert Model.__slots__ == {'_foo'}
    if platform.python_implementation() == 'PyPy':
        repr(Model._foo).startswith('<member_descriptor object at')
    else:
        assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"

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
    if platform.python_implementation() == 'PyPy':
        repr(Model._foo).startswith('<member_descriptor object at')
    else:
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

    assert Model.__slots__ == {'_foo'}
    if platform.python_implementation() == 'PyPy':
        repr(Model._foo).startswith('<member_descriptor object at')
    else:
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


def test_underscore_attrs_are_private():
    class Model(BaseModel):
        _foo: str = 'abc'
        _bar: ClassVar[str] = 'cba'

    assert Model.__slots__ == {'_foo'}
    if platform.python_implementation() == 'PyPy':
        repr(Model._foo).startswith('<member_descriptor object at')
    else:
        assert repr(Model._foo) == "<member '_foo' of 'Model' objects>"
    assert Model._bar == 'cba'
    assert Model.__private_attributes__ == {'_foo': PrivateAttr('abc')}

    m = Model()
    assert m._foo == 'abc'
    m._foo = None
    assert m._foo is None

    with pytest.raises(
        AttributeError,
        match=(
            '"_bar" is a ClassVar of `Model` and cannot be set on an instance. '
            'If you want to set a value on the class, use `Model._bar = value`.'
        ),
    ):
        m._bar = 1


def test_private_attribute_intersection_with_extra_field():
    class Model(BaseModel):
        _foo = PrivateAttr('private_attribute')

        model_config = ConfigDict(extra='allow')

    assert Model.__slots__ == {'_foo'}
    m = Model(_foo='field')
    assert m._foo == 'private_attribute'
    assert m.__dict__ == {}
    assert m.__pydantic_extra__ == {'_foo': 'field'}
    assert m.model_dump() == {'_foo': 'field'}

    m._foo = 'still_private'
    assert m._foo == 'still_private'
    assert m.__dict__ == {}
    assert m.__pydantic_extra__ == {'_foo': 'field'}
    assert m.model_dump() == {'_foo': 'field'}


def test_private_attribute_invalid_name():
    with pytest.raises(
        NameError,
        match='Private attributes "foo" must not be a valid field name; use sunder names, e.g. "_foo"',
    ):

        class Model(BaseModel):
            foo = PrivateAttr()


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
    m1 = Model()
    m2 = Model()

    for attr in Model.__slots__:
        assert object.__getattribute__(m1, attr) == 'spam'

    # In v2, you are always allowed to set instance attributes if the name starts with `_`.
    m1._bar = 'not spam'
    assert m1._bar == 'not spam'
    assert m2._bar == 'spam'

    with pytest.raises(ValueError, match='"Model" object has no field "foo"'):
        m1.foo = 'not spam'


def test_default_and_default_factory_used_error():
    with pytest.raises(TypeError, match='cannot specify both default and default_factory'):
        PrivateAttr(default=123, default_factory=lambda: 321)


def test_config_override_init():
    class MyModel(BaseModel):
        x: str
        _private_attr: int

        def __init__(self, **data) -> None:
            super().__init__(**data)
            self._private_attr = 123

    m = MyModel(x='hello')
    assert m.model_dump() == {'x': 'hello'}
    assert m._private_attr == 123


def test_generic_private_attribute():
    T = TypeVar('T')

    class Model(BaseModel, Generic[T]):
        value: T
        _private_value: T

    m = Model[int](value=1, _private_attr=3)
    m._private_value = 3
    assert m.model_dump() == {'value': 1}


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
    if platform.python_implementation() == 'PyPy':
        assert repr(Model._foo).startswith('<member_descriptor object at')
        assert repr(Model._bar).startswith('<member_descriptor object at')
        assert repr(Model._baz).startswith('<member_descriptor object at')
    else:
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


def test_private_attributes_not_dunder() -> None:
    with pytest.raises(
        NameError,
        match='Private attributes "__foo__" must not have dunder names; use a single underscore prefix instead.',
    ):

        class MyModel(BaseModel):
            __foo__ = PrivateAttr({'private'})


def test_ignored_types_are_ignored() -> None:
    class IgnoredType:
        pass

    class MyModel(BaseModel):
        model_config = ConfigDict(ignored_types=(IgnoredType,))

        _a = IgnoredType()
        _b: int = IgnoredType()
        _c: IgnoredType
        _d: IgnoredType = IgnoredType()

        # The following are included to document existing behavior, and can be updated
        # if the current behavior does not match the desired behavior
        _e: int
        _f: int = 1
        _g = 1  # Note: this is completely ignored, in keeping with v1

    assert sorted(MyModel.__private_attributes__.keys()) == ['_e', '_f']


@pytest.mark.skipif(not hasattr(functools, 'cached_property'), reason='cached_property is not available')
def test_ignored_types_are_ignored_cached_property():
    """Demonstrate the members of functools are ignore here as with fields."""

    class MyModel(BaseModel):
        _a: functools.cached_property
        _b: int

    assert set(MyModel.__private_attributes__) == {'_b'}
