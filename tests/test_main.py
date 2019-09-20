from enum import Enum
from typing import Any, ClassVar, List, Mapping, Type

import pytest

from pydantic import BaseModel, Extra, Field, NoneBytes, NoneStr, Required, ValidationError, constr


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
    assert '"UltraSimpleModel" object has no field "c"' in exc_info.value.args[0]


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

    assert list(Model.__fields__.keys()) == ['c', 'b', 'a', 'd']


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
    assert '"TestModel" object has no field "b"' in exc_info.value.args[0]


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
    assert '"TestModel" is immutable and does not support item assignment' in exc_info.value.args[0]
    with pytest.raises(ValueError) as exc_info:
        m.b = 11
    assert '"TestModel" object has no field "b"' in exc_info.value.args[0]


def test_const_validates():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    m = Model(a=3)
    assert m.a == 3


def test_const_uses_default():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    m = Model()
    assert m.a == 3


def test_const_with_wrong_value():
    class Model(BaseModel):
        a: int = Field(3, const=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=4)

    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'unexpected value; permitted: 3',
            'type': 'value_error.const',
            'ctx': {'given': 4, 'permitted': [3]},
        }
    ]


def test_const_list():
    class SubModel(BaseModel):
        b: int

    class Model(BaseModel):
        a: List[SubModel] = Field([SubModel(b=1), SubModel(b=2), SubModel(b=3)], const=True)
        b: List[SubModel] = Field([{'b': 4}, {'b': 5}, {'b': 6}], const=True)

    m = Model()
    assert m.a == [SubModel(b=1), SubModel(b=2), SubModel(b=3)]
    assert m.b == [SubModel(b=4), SubModel(b=5), SubModel(b=6)]
    assert m.schema() == {
        'definitions': {
            'SubModel': {
                'properties': {'b': {'title': 'B', 'type': 'integer'}},
                'required': ['b'],
                'title': 'SubModel',
                'type': 'object',
            }
        },
        'properties': {
            'a': {
                'const': [SubModel(b=1), SubModel(b=2), SubModel(b=3)],
                'items': {'$ref': '#/definitions/SubModel'},
                'title': 'A',
                'type': 'array',
            },
            'b': {
                'const': [{'b': 4}, {'b': 5}, {'b': 6}],
                'items': {'$ref': '#/definitions/SubModel'},
                'title': 'B',
                'type': 'array',
            },
        },
        'title': 'Model',
        'type': 'object',
    }


def test_const_list_with_wrong_value():
    class SubModel(BaseModel):
        b: int

    class Model(BaseModel):
        a: List[SubModel] = Field([SubModel(b=1), SubModel(b=2), SubModel(b=3)], const=True)
        b: List[SubModel] = Field([{'b': 4}, {'b': 5}, {'b': 6}], const=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a=[{'b': 3}, {'b': 1}, {'b': 2}], b=[{'b': 6}, {'b': 5}])

    assert exc_info.value.errors() == [
        {
            'ctx': {
                'given': [{'b': 3}, {'b': 1}, {'b': 2}],
                'permitted': [[SubModel(b=1), SubModel(b=2), SubModel(b=3)]],
            },
            'loc': ('a',),
            'msg': 'unexpected value; permitted: [<SubModel b=1>, <SubModel b=2>, <SubModel b=3>]',
            'type': 'value_error.const',
        },
        {
            'ctx': {'given': [{'b': 6}, {'b': 5}], 'permitted': [[{'b': 4}, {'b': 5}, {'b': 6}]]},
            'loc': ('b',),
            'msg': "unexpected value; permitted: [{'b': 4}, {'b': 5}, {'b': 6}]",
            'type': 'value_error.const',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a=[SubModel(b=3), SubModel(b=1), SubModel(b=2)], b=[SubModel(b=3), SubModel(b=1)])

    assert exc_info.value.errors() == [
        {
            'ctx': {
                'given': [SubModel(b=3), SubModel(b=1), SubModel(b=2)],
                'permitted': [[SubModel(b=1), SubModel(b=2), SubModel(b=3)]],
            },
            'loc': ('a',),
            'msg': 'unexpected value; permitted: [<SubModel b=1>, <SubModel b=2>, <SubModel b=3>]',
            'type': 'value_error.const',
        },
        {
            'ctx': {'given': [SubModel(b=3), SubModel(b=1)], 'permitted': [[{'b': 4}, {'b': 5}, {'b': 6}]]},
            'loc': ('b',),
            'msg': "unexpected value; permitted: [{'b': 4}, {'b': 5}, {'b': 6}]",
            'type': 'value_error.const',
        },
    ]


def test_const_validation_json_serializable():
    class SubForm(BaseModel):
        field: int

    class Form(BaseModel):
        field1: SubForm = Field({'field': 2}, const=True)
        field2: List[SubForm] = Field([{'field': 2}], const=True)

    with pytest.raises(ValidationError) as exc_info:
        # Fails
        Form(field1={'field': 1}, field2=[{'field': 1}])

    # This should not raise an Json error
    exc_info.value.json()


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


def test_type_type_validation_success():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    arbitrary_type_class = ArbitraryType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_subclass_validation_success():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    class ArbitrarySubType(ArbitraryType):
        pass

    arbitrary_type_class = ArbitrarySubType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_type_type_validation_fails_for_instance():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    class C:
        pass

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=C)
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'subclass of ArbitraryType expected',
            'type': 'type_error.subclass',
            'ctx': {'expected_class': 'ArbitraryType'},
        }
    ]


def test_type_type_validation_fails_for_basic_type():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type[ArbitraryType]

    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=1)
    assert exc_info.value.errors() == [
        {
            'loc': ('t',),
            'msg': 'subclass of ArbitraryType expected',
            'type': 'type_error.subclass',
            'ctx': {'expected_class': 'ArbitraryType'},
        }
    ]


def test_bare_type_type_validation_success():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type

    arbitrary_type_class = ArbitraryType
    m = ArbitraryClassAllowedModel(t=arbitrary_type_class)
    assert m.t == arbitrary_type_class


def test_bare_type_type_validation_fails():
    class ArbitraryClassAllowedModel(BaseModel):
        t: Type

    arbitrary_type = ArbitraryType()
    with pytest.raises(ValidationError) as exc_info:
        ArbitraryClassAllowedModel(t=arbitrary_type)
    assert exc_info.value.errors() == [{'loc': ('t',), 'msg': 'a class is expected', 'type': 'type_error.class'}]


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
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

        class Config:
            allow_population_by_alias = True

    m = MyModel(alias_a='a')

    assert m.dict(skip_defaults=True) == {'a': 'a'}
    assert m.dict(skip_defaults=True, by_alias=True) == {'alias_a': 'a'}


def test_dict_skip_defaults_populated_by_alias_with_extra():
    class MyModel(BaseModel):
        a: str = Field('default', alias='alias_a')
        b: str = Field('default', alias='alias_b')

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
        a: str = Field(None, alias='alias_a')

        class Config:
            extra = Extra.allow

    m = MyModel(extra_key='extra')
    assert m.dict() == {'a': None, 'extra_key': 'extra'}
    assert m.dict(by_alias=True) == {'alias_a': None, 'extra_key': 'extra'}


def test_alias_generator():
    def to_camel(string: str):
        return ''.join(x.capitalize() for x in string.split('_'))

    class MyModel(BaseModel):
        a: List[str] = None
        foo_bar: str

        class Config:
            alias_generator = to_camel

    data = {'A': ['foo', 'bar'], 'FooBar': 'foobar'}
    v = MyModel(**data)
    assert v.a == ['foo', 'bar']
    assert v.foo_bar == 'foobar'
    assert v.dict(by_alias=True) == data


def test_alias_generator_with_field_schema():
    def to_upper_case(string: str):
        return string.upper()

    class MyModel(BaseModel):
        my_shiny_field: Any  # Alias from Config.fields will be used
        foo_bar: str  # Alias from Config.fields will be used
        baz_bar: str  # Alias will be generated
        another_field: str  # Alias will be generated

        class Config:
            alias_generator = to_upper_case
            fields = {'my_shiny_field': 'MY_FIELD', 'foo_bar': {'alias': 'FOO'}, 'another_field': {'not_alias': 'a'}}

    data = {'MY_FIELD': ['a'], 'FOO': 'bar', 'BAZ_BAR': 'ok', 'ANOTHER_FIELD': '...'}
    m = MyModel(**data)
    assert m.dict(by_alias=True) == data


def test_alias_generator_wrong_type_error():
    def return_bytes(string):
        return b'not a string'

    with pytest.raises(TypeError) as e:

        class MyModel(BaseModel):
            bar: Any

            class Config:
                alias_generator = return_bytes

    assert str(e.value) == "Config.alias_generator must return str, not <class 'bytes'>"


def test_root():
    class MyModel(BaseModel):
        __root__: str

    m = MyModel(__root__='a')
    assert m.dict() == {'__root__': 'a'}
    assert m.__root__ == 'a'


def test_root_list():
    class MyModel(BaseModel):
        __root__: List[str]

    m = MyModel(__root__=['a'])
    assert m.dict() == {'__root__': ['a']}
    assert m.__root__ == ['a']


def test_root_failed():
    with pytest.raises(ValueError, match='__root__ cannot be mixed with other fields'):

        class MyModel(BaseModel):
            __root__: str
            a: str


def test_root_undefined_failed():
    class MyModel(BaseModel):
        a: List[str]

    with pytest.raises(ValidationError) as exc_info:
        MyModel(__root__=['a'])
        assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_parse_root_as_mapping():
    with pytest.raises(TypeError, match='custom root type cannot allow mapping'):

        class MyModel(BaseModel):
            __root__: Mapping[str, str]


def test_untouched_types():
    from pydantic import BaseModel

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    class Model(BaseModel):
        class Config:
            keep_untouched = (classproperty,)

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    assert Model.class_name == 'Model'
    assert Model().class_name == 'Model'


def test_custom_types_fail_without_keep_untouched():
    from pydantic import BaseModel

    class _ClassPropertyDescriptor:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    classproperty = _ClassPropertyDescriptor

    with pytest.raises(RuntimeError) as e:

        class Model(BaseModel):
            @classproperty
            def class_name(cls) -> str:
                return cls.__name__

        Model.class_name

    assert str(e.value) == (
        "no validator found for <class 'tests.test_main.test_custom_types_fail_without_keep_untouched.<locals>."
        "_ClassPropertyDescriptor'> see `keep_untouched` or `arbitrary_types_allowed` in Config"
    )

    class Model(BaseModel):
        class Config:
            arbitrary_types_allowed = True

        @classproperty
        def class_name(cls) -> str:
            return cls.__name__

    with pytest.raises(AttributeError) as e:
        Model.class_name
    assert str(e.value) == "type object 'Model' has no attribute 'class_name'"


def test_model_iteration():
    class Foo(BaseModel):
        a: int = 1
        b: int = 2

    class Bar(BaseModel):
        c: int
        d: Foo

    m = Bar(c=3, d={})
    assert m.dict() == {'c': 3, 'd': {'a': 1, 'b': 2}}
    assert list(m) == [('c', 3), ('d', Foo())]
    assert dict(m) == {'c': 3, 'd': Foo()}
