from typing import Optional, Tuple

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PydanticUserError,
    ValidationError,
    create_model,
    errors,
    field_validator,
)
from pydantic.decorators import validator
from pydantic.fields import ModelPrivateAttr


def test_create_model():
    model = create_model('FooModel', foo=(str, ...), bar=(int, 123))
    assert issubclass(model, BaseModel)
    assert model.model_config == BaseModel.model_config
    assert model.__name__ == 'FooModel'
    assert model.model_fields.keys() == {'foo', 'bar'}

    assert not model.__pydantic_decorators__.validator
    assert not model.__pydantic_decorators__.root_validator
    assert not model.__pydantic_decorators__.field_validator
    assert not model.__pydantic_decorators__.field_serializer

    assert model.__module__ == 'pydantic.main'


def test_create_model_usage():
    model = create_model('FooModel', foo=(str, ...), bar=(int, 123))
    m = model(foo='hello')
    assert m.foo == 'hello'
    assert m.bar == 123
    with pytest.raises(ValidationError):
        model()
    with pytest.raises(ValidationError):
        model(foo='hello', bar='xxx')


def test_create_model_pickle(create_module):
    """
    Pickle will work for dynamically created model only if it was defined globally with its class name
    and module where it's defined was specified
    """

    @create_module
    def module():
        import pickle

        from pydantic import create_model

        FooModel = create_model('FooModel', foo=(str, ...), bar=(int, 123), __module__=__name__)

        m = FooModel(foo='hello')
        d = pickle.dumps(m)
        m2 = pickle.loads(d)
        assert m2.foo == m.foo == 'hello'
        assert m2.bar == m.bar == 123
        assert m2 == m
        assert m2 is not m


def test_invalid_name():
    with pytest.warns(RuntimeWarning):
        model = create_model('FooModel', _foo=(str, ...))
    assert len(model.model_fields) == 0


def test_field_wrong_tuple():
    with pytest.raises(errors.PydanticUserError):
        create_model('FooModel', foo=(1, 2, 3))


def test_config_and_base():
    with pytest.raises(errors.PydanticUserError):
        create_model('FooModel', __config__=BaseModel.model_config, __base__=BaseModel)


def test_inheritance():
    class BarModel(BaseModel):
        x: int = 1
        y: int = 2

    model = create_model('FooModel', foo=(str, ...), bar=(int, 123), __base__=BarModel)
    assert model.model_fields.keys() == {'foo', 'bar', 'x', 'y'}
    m = model(foo='a', x=4)
    assert m.model_dump() == {'bar': 123, 'foo': 'a', 'x': 4, 'y': 2}


def test_custom_config():
    config = ConfigDict(frozen=True)
    expected_config = BaseModel.model_config.copy()
    expected_config['frozen'] = True

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    m = model(**{'foo': '987'})
    assert m.foo == 987
    assert model.model_config == expected_config
    with pytest.raises(TypeError):
        m.foo = 654


def test_custom_config_inherits():
    class Config(ConfigDict):
        custom_config: bool

    config = Config(custom_config=True, validate_assignment=True)
    expected_config = Config(BaseModel.model_config)
    expected_config.update(config)

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    m = model(**{'foo': '987'})
    assert m.foo == 987
    assert model.model_config == expected_config
    with pytest.raises(ValidationError):
        m.foo = ['123']


def test_custom_config_extras():
    config = ConfigDict(extra='forbid')

    model = create_model('FooModel', foo=(int, ...), __config__=config)
    assert model(foo=654)
    with pytest.raises(ValidationError):
        model(bar=654)


def test_inheritance_validators():
    class BarModel(BaseModel):
        @field_validator('a', check_fields=False)
        @classmethod
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a=(str, 'cake'), __base__=BarModel)
    assert model().a == 'cake'
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_always():
    class BarModel(BaseModel):
        @field_validator('a', check_fields=False)
        @classmethod
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a=(str, Field('cake', validate_default=True)), __base__=BarModel)
    with pytest.raises(ValidationError):
        model()
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_all():
    with pytest.warns(DeprecationWarning, match='Pydantic V1 style `@validator` validators are deprecated'):

        class BarModel(BaseModel):
            @validator('*')
            @classmethod
            def check_all(cls, v):
                return v * 2

    model = create_model('FooModel', a=(int, ...), b=(int, ...), __base__=BarModel)
    assert model(a=2, b=6).model_dump() == {'a': 4, 'b': 12}


def test_funky_name():
    model = create_model('FooModel', **{'this-is-funky': (int, ...)})
    m = model(**{'this-is-funky': '123'})
    assert m.model_dump() == {'this-is-funky': 123}
    with pytest.raises(ValidationError) as exc_info:
        model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('this-is-funky',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_repeat_base_usage():
    class Model(BaseModel):
        a: str

    assert Model.model_fields.keys() == {'a'}

    model = create_model('FooModel', b=(int, 1), __base__=Model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}

    model2 = create_model('Foo2Model', c=(int, 1), __base__=Model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}
    assert model2.model_fields.keys() == {'a', 'c'}

    model3 = create_model('Foo2Model', d=(int, 1), __base__=model)

    assert Model.model_fields.keys() == {'a'}
    assert model.model_fields.keys() == {'a', 'b'}
    assert model2.model_fields.keys() == {'a', 'c'}
    assert model3.model_fields.keys() == {'a', 'b', 'd'}


def test_dynamic_and_static():
    class A(BaseModel):
        x: int
        y: float
        z: str

    DynamicA = create_model('A', x=(int, ...), y=(float, ...), z=(str, ...))

    for field_name in ('x', 'y', 'z'):
        assert A.model_fields[field_name].default == DynamicA.model_fields[field_name].default


def test_config_field_info_create_model():
    # TODO fields doesn't exist anymore, remove test?
    # class Config:
    #     fields = {'a': {'description': 'descr'}}
    ConfigDict()

    m1 = create_model('M1', __config__={'title': 'abc'}, a=(str, ...))
    assert m1.model_json_schema() == {
        'properties': {'a': {'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'abc',
        'type': 'object',
    }

    m2 = create_model('M2', __config__={}, a=(str, Field(description='descr')))
    assert m2.model_json_schema() == {
        'properties': {'a': {'description': 'descr', 'title': 'A', 'type': 'string'}},
        'required': ['a'],
        'title': 'M2',
        'type': 'object',
    }


@pytest.mark.parametrize('base', [ModelPrivateAttr, object])
def test_set_name(base):
    calls = []

    class class_deco(base):
        def __init__(self, fn):
            super().__init__()
            self.fn = fn

        def __set_name__(self, owner, name):
            calls.append((owner, name))

        def __get__(self, obj, type=None):
            return self.fn(obj) if obj else self

    class A(BaseModel):
        x: int

        @class_deco
        def _some_func(self):
            return self.x

    assert calls == [(A, '_some_func')]
    a = A(x=2)

    # we don't test whether calling the method on a PrivateAttr works:
    # attribute access on privateAttributes is more complicated, it doesn't
    # get added to the class namespace (and will also get set on the instance
    # with _init_private_attributes), so the descriptor protocol won't work.
    if base is object:
        assert a._some_func == 2


def test_create_model_with_slots():
    field_definitions = {'__slots__': (Optional[Tuple[str, ...]], None), 'foobar': (Optional[int], None)}
    with pytest.warns(RuntimeWarning, match='__slots__ should not be passed to create_model'):
        model = create_model('PartialPet', **field_definitions)

    assert model.model_fields.keys() == {'foobar'}


def test_create_model_non_annotated():
    with pytest.raises(
        TypeError,
        match='A non-annotated attribute was detected: `bar = 123`. All model fields require a type annotation',
    ):
        create_model('FooModel', foo=(str, ...), bar=123)


def test_create_model_tuple():
    model = create_model('FooModel', foo=(Tuple[int, int], (1, 2)))
    assert model().foo == (1, 2)
    assert model(foo=(3, 4)).foo == (3, 4)


def test_create_model_tuple_3():
    with pytest.raises(PydanticUserError, match=r'^Field definitions should either be a `\(<type>, <default>\)`\.\n'):
        create_model('FooModel', foo=(Tuple[int, int], (1, 2), 'more'))
