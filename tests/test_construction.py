import pickle
from copy import deepcopy
from typing import Annotated, Any

import pytest
from pydantic_core import PydanticUndefined, ValidationError

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field, PrivateAttr


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
    with pytest.warns(
        UserWarning,
        match=r"Expected `int` - serialized value may not be as expected \[field_name='b', input_value='foobar', input_type=str\]",
    ):
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


def test_simple_copy():
    m = Model(a=24)
    m2 = m.model_copy()

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m == m2


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
    m2 = m.model_copy(deep=True)

    assert m.a == m2.a == 24
    assert m.b == m2.b == 10
    assert m.c == m2.c == 'foobar'
    assert m.d is not m2.d
    assert m == m2
    assert m._foo_ == m2._foo_
    assert m._foo_ is not m2._foo_


def test_copy_update(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.model_copy(update={'a': 'different'})

    assert m.a == 24
    assert m2.a == 'different'
    m_keys = m.model_dump().keys()
    with pytest.warns(
        UserWarning,
        match=r"Expected `float` - serialized value may not be as expected \[field_name='a', input_value='different', input_type=str\]",
    ):
        m2_keys = m2.model_dump().keys()
    assert set(m_keys) == set(m2_keys) == {'a', 'b', 'c', 'd'}
    assert m != m2


def test_copy_update_unset():
    class Foo(BaseModel):
        foo: str | None = None
        bar: str | None = None

    assert (
        Foo(foo='hello').model_copy(update={'bar': 'world'}).model_dump_json(exclude_unset=True)
        == '{"foo":"hello","bar":"world"}'
    )


class ExtraModel(BaseModel, extra='allow'):
    pass


def test_copy_deep_extra():
    class Foo(BaseModel, extra='allow'):
        pass

    m = Foo(extra=[])
    assert m.model_copy().extra is m.extra
    assert m.model_copy(deep=True).extra == m.extra
    assert m.model_copy(deep=True).extra is not m.extra


class NotDeepCopyable:
    def __deepcopy__(self, memo):
        raise TypeError('This object cannot be deepcopied')


def test_model_copy_deep_update_skips_deepcopy_of_updated_fields() -> None:

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        name: str = 'default'
        arbitrary: Any = None

    model = Model(arbitrary=NotDeepCopyable())

    copied = model.model_copy(deep=True, update={'arbitrary': None})
    assert copied.arbitrary is None
    assert copied.name == 'default'
    assert copied is not model


def test_model_copy_deep_update_preserves_shared_references() -> None:

    class Inner(BaseModel):
        x: int = 0

    class Outer(BaseModel):
        a: Inner
        b: Inner
        c: Inner

    shared = Inner(x=1)
    m = Outer(a=shared, b=shared, c=Inner(x=2))
    m2 = m.model_copy(deep=True, update={'c': Inner(x=99)})

    assert m2.a is not shared
    assert m2.a is m2.b
    assert m2.c.x == 99
    assert m.a is shared


def test_model_copy_deep_update_skips_deepcopy_of_extra_fields() -> None:
    """Extra fields present in `update` should not be deepcopied."""

    class Foo(BaseModel, extra='allow'):
        pass

    m = Foo(extra_field=NotDeepCopyable(), other=[1, 2, 3])

    copied = m.model_copy(deep=True, update={'extra_field': 'replaced'})
    assert copied.extra_field == 'replaced'
    assert copied.other == [1, 2, 3]
    assert copied.other is not m.other


def test_model_copy_deep_update_with_private_attributes() -> None:
    """Ensure private attributes are deepcopied when `deep=True` and `update` are provided."""

    class M(BaseModel):
        a: int
        _private = PrivateAttr({'private'})

    m = M(a=1)
    m._private = {'modified'}
    m2 = m.model_copy(deep=True, update={'a': 2})

    assert m2.a == 2
    assert m2._private == {'modified'}
    assert m2._private is not m._private


def test_deepcopy_self_referential_model() -> None:
    class Node(BaseModel, extra='allow'):
        child: 'Node | None' = None
        _private: Any = PrivateAttr(None)

    original = Node()
    original.child = original
    original.extra_child = original
    original._private = original

    for copied in (
        deepcopy(original),
        original.model_copy(deep=True),
        original.model_copy(deep=True, update={'extra_child': None}),
    ):
        assert copied is not original
        assert copied.child is copied
        assert copied._private is copied


def test_deepcopy_mutually_referential_models() -> None:
    class Node(BaseModel):
        other: 'Node | None' = None

    a = Node()
    b = Node(other=a)
    a.other = b

    copied = deepcopy(a)

    assert copied is not a
    assert copied.other is not b
    assert copied.other.other is copied


def test_copy_set_fields(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='12'))
    m2 = m.model_copy()

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


def test_copy_undefined(ModelTwo):
    m = ModelTwo(a=24, d=Model(a='123.45'))
    m2 = m.model_copy()
    assert m2._foo_ == {'private'}

    m._foo_ = PydanticUndefined
    m3 = m.model_copy()
    assert not hasattr(m3, '_foo_')


def test_immutable_copy_with_frozen():
    class Model(BaseModel):
        model_config = ConfigDict(frozen=True)
        a: int
        b: int

    m = Model(a=40, b=10)
    assert m == m.model_copy()
    assert repr(m) == 'Model(a=40, b=10)'

    m2 = m.model_copy(update={'b': 12})
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


def test_shallow_copy_modify():
    class X(BaseModel):
        val: int
        deep: Any

    x = X(val=1, deep={'deep_thing': [1, 2]})

    y = x.model_copy()
    y.val = 2
    y.deep['deep_thing'].append(3)

    assert x.val == 1
    assert y.val == 2
    # deep['deep_thing'] gets modified
    assert x.deep['deep_thing'] == [1, 2, 3]
    assert y.deep['deep_thing'] == [1, 2, 3]


def test_construct_default_factory():
    class Model(BaseModel):
        foo: list[int] = Field(default_factory=list)
        bar: str = 'Baz'

    m = Model.model_construct()
    assert m.foo == []
    assert m.bar == 'Baz'


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


@pytest.mark.xfail(
    reason='`model_construct()` does not rebuild incomplete models, and relies on `FieldInfo` instances '
    'that may be incomplete (here, the `Field()` metadata is part of the unevaluated annotation).',
)
def test_model_construct_incomplete_model() -> None:
    # When making this test work, look at `test_string_annotation_union_type()` which assumes `model_construct()`
    # doesn't rebuild the model.
    class Model(BaseModel):
        a: 'Annotated[Later | None, Field(alias="A")]'
        b: 'Annotated[Later | None, Field(default=None)]'

    class Later(BaseModel):
        pass

    assert Model.__pydantic_complete__ is False

    later = Later()
    m = Model.model_construct(A=later)
    assert m.a is later
    assert m.b is None
    assert m.model_fields_set == {'a'}
