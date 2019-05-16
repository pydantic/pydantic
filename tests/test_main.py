from enum import Enum
from typing import Any, ClassVar, List

import pytest

from pydantic import BaseModel, Extra, NoneBytes, NoneStr, Required, Schema, ValidationError, constr


def test_success():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float
        b: int = 10

    m = Model(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


class UltraSimpleModel(BaseModel):
    a: float = ...
    b: int = 10


def test_ultra_simple_missing():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert repr(m) == '<UltraSimpleModel a=10.2 b=10>'
    assert repr(m.fields['a']) == '<Field(a type=float required)>'
    assert dict(m) == {'a': 10.2, 'b': 10}
    assert m.dict() == {'a': 10.2, 'b': 10}
    assert m.json() == '{"a": 10.2, "b": 10}'


def test_str_truncate():
    class Model(BaseModel):
        s1: str
        s2: str
        b1: bytes
        b2: bytes

    m = Model(s1='132', s2='x' * 100, b1='123', b2='x' * 100)
    print(repr(m.to_string()))
    assert m.to_string() == (
        "Model s1='132' "
        "s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…' "
        "b1=b'123' "
        "b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…"
    )
    assert """\
Model
  s1='132'
  s2='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…'
  b1=b'123'
  b2=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx…""" == m.to_string(
        pretty=True
    )


def test_comparing():
    m = UltraSimpleModel(a=10.2, b='100')
    assert m == {'a': 10.2, 'b': 100}
    assert m == UltraSimpleModel(a=10.2, b=100)


def test_nullable_strings_success():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    m = NoneCheckModel(
        required_str_value='v1', required_str_none_value=None, required_bytes_value='v2', required_bytes_none_value=None
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails():
    class NoneCheckModel(BaseModel):
        existing_str_value = 'foo'
        required_str_value: str = ...
        required_str_none_value: NoneStr = ...
        existing_bytes_value = b'foo'
        required_bytes_value: bytes = ...
        required_bytes_none_value: NoneBytes = ...

    with pytest.raises(ValidationError) as exc_info:
        NoneCheckModel(
            required_str_value=None,
            required_str_none_value=None,
            required_bytes_value=None,
            required_bytes_none_value=None,
        )
    assert exc_info.value.errors() == [
        {'loc': ('required_str_value',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
        {
            'loc': ('required_bytes_value',),
            'msg': 'none is not an allowed value',
            'type': 'type_error.none.not_allowed',
        },
    ]


class RecursiveModel(BaseModel):
    grape: bool = ...
    banana: UltraSimpleModel = ...


def test_recursion():
    m = RecursiveModel(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == '<RecursiveModel grape=True banana=<UltraSimpleModel a=1.0 b=10>>'


def test_recursion_fails():
    with pytest.raises(ValidationError):
        RecursiveModel(grape=1, banana=123)


def test_not_required():
    class Model(BaseModel):
        a: float = None

    assert Model(a=12.2).a == 12.2
    assert Model().a is None
    assert Model(a=None).a is None


def test_infer_type():
    class Model(BaseModel):
        a = False
        b = ''
        c = 0

    assert Model().a is False
    assert Model().b == ''
    assert Model().c == 0


def test_allow_extra():
    class Model(BaseModel):
        a: float = ...

        class Config:
            extra = Extra.allow

    assert Model(a='10.2', b=12).dict() == {'a': 10.2, 'b': 12}


def test_forbidden_extra_success():
    class ForbiddenExtra(BaseModel):
        foo = 'whatever'

        class Config:
            extra = Extra.forbid

    m = ForbiddenExtra()
    assert m.foo == 'whatever'

    m = ForbiddenExtra(foo=1)
    assert m.foo == '1'


def test_forbidden_extra_fails():
    class ForbiddenExtra(BaseModel):
        foo = 'whatever'

        class Config:
            extra = Extra.forbid

    with pytest.raises(ValidationError) as exc_info:
        ForbiddenExtra(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.errors() == [
        {'loc': ('bar',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
        {'loc': ('spam',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_disallow_mutation():
    class Model(BaseModel):
        a: float

    model = Model(a=0.2)
    with pytest.raises(ValueError, match='"Model" object has no field "b"'):
        model.b = 2


def test_extra_allowed():
    class Model(BaseModel):
        a: float

        class Config:
            extra = Extra.allow

    model = Model(a=0.2, b=0.1)
    assert model.b == 0.1

    assert not hasattr(model, 'c')
    model.c = 1
    assert hasattr(model, 'c')
    assert model.c == 1


def test_extra_ignored():
    class Model(BaseModel):
        a: float

        class Config:
            extra = Extra.ignore

    model = Model(a=0.2, b=0.1)
    assert not hasattr(model, 'b')

    with pytest.raises(ValueError, match='"Model" object has no field "c"'):
        model.c = 1


def test_set_attr():
    m = UltraSimpleModel(a=10.2)
    assert m.dict() == {'a': 10.2, 'b': 10}

    m.b = 20
    assert m.dict() == {'a': 10.2, 'b': 20}


def test_set_attr_invalid():
    class UltraSimpleModel(BaseModel):
        a: float = ...
        b: int = 10

    m = UltraSimpleModel(a=10.2)
    assert m.dict() == {'a': 10.2, 'b': 10}

    with pytest.raises(ValueError) as exc_info:
        m.c = 20
    assert '"UltraSimpleModel" object has no field "c"' in str(exc_info)


def test_any():
    class AnyModel(BaseModel):
        a: Any = 10

    assert AnyModel().a == 10
    assert AnyModel(a='foobar').a == 'foobar'


def test_alias():
    class SubModel(BaseModel):
        c = 'barfoo'

        class Config:
            fields = {'c': {'alias': '_c'}}

    class Model(BaseModel):
        a = 'foobar'
        b: SubModel = SubModel()

        class Config:
            fields = {'a': {'alias': '_a'}}

    assert Model().a == 'foobar'
    assert Model().b.c == 'barfoo'
    assert Model().dict() == {'a': 'foobar', 'b': {'c': 'barfoo'}}
    assert Model(_a='different').a == 'different'
    assert Model(b={'_c': 'different'}).b.c == 'different'
    assert Model(_a='different', b={'_c': 'different'}).dict() == {'a': 'different', 'b': {'c': 'different'}}
    assert Model(_a='different', b={'_c': 'different'}).dict(by_alias=True) == {
        '_a': 'different',
        'b': {'_c': 'different'},
    }


def test_population_by_alias():
    class Model(BaseModel):
        a: str

        class Config:
            allow_population_by_alias = True
            fields = {'a': {'alias': '_a'}}

    assert Model(a='different').a == 'different'
    assert Model(a='different').dict() == {'a': 'different'}
    assert Model(a='different').dict(by_alias=True) == {'_a': 'different'}


def test_field_order():
    class Model(BaseModel):
        c: float
        b: int = 10
        a: str
        d: dict = {}

    # fields are ordered as defined except annotation-only fields come last
    assert list(Model.__fields__.keys()) == ['c', 'a', 'b', 'd']


def test_required():
    # same as below but defined here so class definition occurs inside the test
    class Model(BaseModel):
        a: float = Required
        b: int = 10

    m = Model(a=10.2)
    assert m.dict() == dict(a=10.2, b=10)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_not_immutability():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = True
            extra = Extra.forbid

    m = TestModel()
    assert m.a == 10
    m.a = 11
    assert m.a == 11
    with pytest.raises(ValueError) as exc_info:
        m.b = 11
    assert '"TestModel" object has no field "b"' in str(exc_info)


def test_immutability():
    class TestModel(BaseModel):
        a: int = 10

        class Config:
            allow_mutation = False
            extra = Extra.forbid

    m = TestModel()
    assert m.a == 10
    with pytest.raises(TypeError) as exc_info:
        m.a = 11
    assert '"TestModel" is immutable and does not support item assignment' in str(exc_info)
    with pytest.raises(ValueError) as exc_info:
        m.b = 11
    assert '"TestModel" object has no field "b"' in str(exc_info)


def test_const_validates():
    class Model(BaseModel):
        a: int = Schema(3, const=True)

    m = Model(a=3)
    assert m.a == 3


def test_const_uses_default():
    class Model(BaseModel):
        a: int = Schema(3, const=True)

    m = Model()
    assert m.a == 3


def test_const_with_wrong_value():
    class Model(BaseModel):
        a: int = Schema(3, const=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=4)

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'expected constant value 3',
            'type': 'value_error.const',
            'ctx': {'given': 4, 'const': 3},
        }
    ]


class ValidateAssignmentModel(BaseModel):
    a: int = 2
    b: constr(min_length=1)

    class Config:
        validate_assignment = True


def test_validating_assignment_pass():
    p = ValidateAssignmentModel(a=5, b='hello')
    p.a = 2
    assert p.a == 2
    assert p.dict() == {'a': 2, 'b': 'hello'}
    p.b = 'hi'
    assert p.b == 'hi'
    assert p.dict() == {'a': 2, 'b': 'hi'}


def test_validating_assignment_fail():
    p = ValidateAssignmentModel(a=5, b='hello')

    with pytest.raises(ValidationError) as exc_info:
        p.a = 'b'
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        p.b = ''
    assert exc_info.value.errors() == [
        {
            'loc': ('b',),
            'msg': 'ensure this value has at least 1 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 1},
        }
    ]


def test_enum_values():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Model(BaseModel):
        foo: FooEnum = None

        class Config:
            use_enum_values = True

    m = Model(foo='foo')
    # this is the actual value, so has not "values" field
    assert not isinstance(m.foo, FooEnum)
    assert m.foo == 'foo'


def test_enum_raw():
    FooEnum = Enum('FooEnum', {'foo': 'foo', 'bar': 'bar'})

    class Model(BaseModel):
        foo: FooEnum = None

    m = Model(foo='foo')
    assert isinstance(m.foo, FooEnum)
    assert m.foo != 'foo'
    assert m.foo.value == 'foo'


def test_set_tuple_values():
    class Model(BaseModel):
        foo: set
        bar: tuple

    m = Model(foo=['a', 'b'], bar=['c', 'd'])
    assert m.foo == {'a', 'b'}
    assert m.bar == ('c', 'd')
    assert m.dict() == {'foo': {'a', 'b'}, 'bar': ('c', 'd')}


def test_default_copy():
    class User(BaseModel):
        friends: List[int] = []

    u1 = User()
    u2 = User()
    assert u1.friends is not u2.friends


class ArbitraryType:
    pass


def test_arbitrary_type_allowed_validation_success():
    class ArbitraryTypeAllowedModel(BaseModel):
        t: ArbitraryType

        class Config:
            arbitrary_types_allowed = True

    arbitrary_type_instance = ArbitraryType()
    m = ArbitraryTypeAllowedModel(t=arbitrary_type_instance)
    assert m.t == arbitrary_type_instance


def test_arbitrary_type_allowed_validation_fails():
    class ArbitraryTypeAllowedModel(BaseModel):
        t: ArbitraryType

        class Config:
            arbitrary_types_allowed = True

    class C:
        pass

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryTypeAllowedModel(t=C())
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'instance of ArbitraryType expected',
            'type': 'type_error.arbitrary_type',
            'ctx': {'expected_arbitrary_type': 'ArbitraryType'},
        }
    ]


def test_arbitrary_types_not_allowed():
    with pytest.raises(RuntimeError) as exc_info:

        class ArbitraryTypeNotAllowedModel(BaseModel):
            t: ArbitraryType

    assert exc_info.value.args[0].startswith('no validator found for')


def test_annotation_field_name_shadows_attribute():
    with pytest.raises(NameError):
        # When defining a model that has an attribute with the name of a built-in attribute, an exception is raised
        class BadModel(BaseModel):
            schema: str  # This conflicts with the BaseModel's schema() class method


def test_value_field_name_shadows_attribute():
    # When defining a model that has an attribute with the name of a built-in attribute, an exception is raised
    with pytest.raises(NameError):

        class BadModel(BaseModel):
            schema = 'abc'  # This conflicts with the BaseModel's schema() class method


def test_class_var():
    class MyModel(BaseModel):
        a: ClassVar
        b: ClassVar[int] = 1
        c: int = 2

    assert list(MyModel.__fields__.keys()) == ['c']


def test_fields_set():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.__fields_set__ == {'a'}

    m.b = 2
    assert m.__fields_set__ == {'a', 'b'}

    m = MyModel(a=5, b=2)
    assert m.__fields_set__ == {'a', 'b'}


def test_skip_defaults_dict():
    class MyModel(BaseModel):
        a: int
        b: int = 2

    m = MyModel(a=5)
    assert m.dict(skip_defaults=True) == {'a': 5}

    m = MyModel(a=5, b=3)
    assert m.dict(skip_defaults=True) == {'a': 5, 'b': 3}


def test_skip_defaults_recursive():
    class ModelA(BaseModel):
        a: int
        b: int = 1

    class ModelB(BaseModel):
        c: int
        d: int = 2
        e: ModelA

    m = ModelB(c=5, e={'a': 0})
    assert m.dict() == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert m.dict(skip_defaults=True) == {'c': 5, 'e': {'a': 0}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}


def test_dict_skip_defaults_populated_by_alias():
    class MyModel(BaseModel):
        a: str = Schema('default', alias='alias_a')
        b: str = Schema('default', alias='alias_b')

        class Config:
            allow_population_by_alias = True

    m = MyModel(alias_a='a')

    assert m.dict(skip_defaults=True) == {'a': 'a'}
    assert m.dict(skip_defaults=True, by_alias=True) == {'alias_a': 'a'}


def test_dict_skip_defaults_populated_by_alias_with_extra():
    class MyModel(BaseModel):
        a: str = Schema('default', alias='alias_a')
        b: str = Schema('default', alias='alias_b')

        class Config:
            extra = 'allow'

    m = MyModel(alias_a='a', c='c')

    assert m.dict(skip_defaults=True) == {'a': 'a', 'c': 'c'}
    assert m.dict(skip_defaults=True, by_alias=True) == {'alias_a': 'a', 'c': 'c'}


def test_dir_fields():
    class MyModel(BaseModel):
        attribute_a: int
        attribute_b: int = 2

    m = MyModel(attribute_a=5)

    assert 'dict' in dir(m)
    assert 'json' in dir(m)
    assert 'attribute_a' in dir(m)
    assert 'attribute_b' in dir(m)


def test_dict_with_extra_keys():
    class MyModel(BaseModel):
        a: str = Schema(None, alias='alias_a')

        class Config:
            extra = Extra.allow

    m = MyModel(extra_key='extra')
    assert m.dict() == {'a': None, 'extra_key': 'extra'}
    assert m.dict(by_alias=True) == {'alias_a': None, 'extra_key': 'extra'}
