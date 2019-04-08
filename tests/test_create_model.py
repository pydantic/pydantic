from typing import List

import pytest

from pydantic import BaseModel, Extra, ValidationError, create_model, errors, validator


def test_create_model():
    model = create_model('FooModel', foo=(str, ...), bar=123)
    assert issubclass(model, BaseModel)
    assert issubclass(model.__config__, BaseModel.Config)
    assert model.__name__ == 'FooModel'
    assert model.__fields__.keys() == {'foo', 'bar'}
    assert model.__validators__ == {}
    assert model.__config__.__name__ == 'Config'


def test_create_model_usage():
    model = create_model('FooModel', foo=(str, ...), bar=123)
    m = model(foo='hello')
    assert m.foo == 'hello'
    assert m.bar == 123
    with pytest.raises(ValidationError):
        model()
    with pytest.raises(ValidationError):
        model(foo='hello', bar='xxx')


def test_invalid_name():
    with pytest.warns(RuntimeWarning):
        model = create_model('FooModel', _foo=(str, ...))
    assert len(model.__fields__) == 0


def test_field_wrong_tuple():
    with pytest.raises(errors.ConfigError):
        create_model('FooModel', foo=(1, 2, 3))


def test_config_and_base():
    with pytest.raises(errors.ConfigError):
        create_model('FooModel', __config__=BaseModel.Config, __base__=BaseModel)


def test_inheritance():
    class BarModel(BaseModel):
        x = 1
        y = 2

    model = create_model('FooModel', foo=(str, ...), bar=(int, 123), __base__=BarModel)
    assert model.__fields__.keys() == {'foo', 'bar', 'x', 'y'}
    m = model(foo='a', x=4)
    assert m.dict() == {'bar': 123, 'foo': 'a', 'x': 4, 'y': 2}


def test_custom_config():
    class Config:
        fields = {'foo': 'api-foo-field'}

    model = create_model('FooModel', foo=(int, ...), __config__=Config)
    assert model(**{'api-foo-field': '987'}).foo == 987
    assert issubclass(model.__config__, BaseModel.Config)
    with pytest.raises(ValidationError):
        model(foo=654)


def test_custom_config_inherits():
    class Config(BaseModel.Config):
        fields = {'foo': 'api-foo-field'}

    model = create_model('FooModel', foo=(int, ...), __config__=Config)
    assert model(**{'api-foo-field': '987'}).foo == 987
    assert issubclass(model.__config__, BaseModel.Config)
    with pytest.raises(ValidationError):
        model(foo=654)


def test_custom_config_extras():
    class Config(BaseModel.Config):
        extra = Extra.forbid

    model = create_model('FooModel', foo=(int, ...), __config__=Config)
    assert model(foo=654)
    with pytest.raises(ValidationError):
        model(bar=654)


def test_inheritance_validators():
    class BarModel(BaseModel):
        @validator('a', check_fields=False)
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a='cake', __base__=BarModel)
    assert model().a == 'cake'
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_always():
    class BarModel(BaseModel):
        @validator('a', check_fields=False, always=True)
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a='cake', __base__=BarModel)
    with pytest.raises(ValidationError):
        model()
    assert model(a='this is foobar good').a == 'this is foobar good'
    with pytest.raises(ValidationError):
        model(a='something else')


def test_inheritance_validators_all():
    class BarModel(BaseModel):
        @validator('*')
        def check_all(cls, v):
            return v * 2

    model = create_model('FooModel', a=(int, ...), b=(int, ...), __base__=BarModel)
    assert model(a=2, b=6).dict() == {'a': 4, 'b': 12}


def test_funky_name():
    model = create_model('FooModel', **{'this-is-funky': (int, ...)})
    m = model(**{'this-is-funky': '123'})
    assert m.dict() == {'this-is-funky': 123}
    with pytest.raises(ValidationError) as exc_info:
        model()
    assert exc_info.value.errors() == [
        {'loc': ('this-is-funky',), 'msg': 'field required', 'type': 'value_error.missing'}
    ]


def test_repeat_base_usage():
    class Model(BaseModel):
        a: str

    assert Model.__fields__.keys() == {'a'}

    model = create_model('FooModel', b=1, __base__=Model)

    assert Model.__fields__.keys() == {'a'}
    assert model.__fields__.keys() == {'a', 'b'}

    model2 = create_model('Foo2Model', c=1, __base__=Model)

    assert Model.__fields__.keys() == {'a'}
    assert model.__fields__.keys() == {'a', 'b'}
    assert model2.__fields__.keys() == {'a', 'c'}

    model3 = create_model('Foo2Model', d=1, __base__=model)

    assert Model.__fields__.keys() == {'a'}
    assert model.__fields__.keys() == {'a', 'b'}
    assert model2.__fields__.keys() == {'a', 'c'}
    assert model3.__fields__.keys() == {'a', 'b', 'd'}


def test_explicit_validators_single():
    @validator('a')
    def check_a(v):
        if 'foobar' not in v:
            raise ValueError('"foobar" not found in a')
        return v

    model = create_model('FooModel', __validators__=[check_a], a=(str, ...), bar=123)
    m = model(a='this is foobar good', bar=456)
    assert m.a == 'this is foobar good'

    with pytest.raises(ValidationError):
        model(a='something else', bar=456)


def test_explicit_validators_multiple():
    @validator('name')
    def name_must_contain_space(v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

    @validator('password2')
    def passwords_match(v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')
        return v

    DynamicUserModel = create_model(
        'DynamicUserModel',
        __validators__=[name_must_contain_space, passwords_match],
        name=(str, ...),
        password1=(str, ...),
        password2=(str, ...),
    )

    with pytest.raises(ValidationError) as exc_info:
        DynamicUserModel(name='FirstSecond', password1=123, password2=234)

    assert exc_info.value.errors() == [
        {'loc': ('name',), 'msg': 'must contain a space', 'type': 'value_error'},
        {'loc': ('password2',), 'msg': 'passwords do not match', 'type': 'value_error'},
    ]


def test_explicit_validators_with_inherited_validators():
    @validator('a', check_fields=False)
    def is_bar_in_a(v):
        if 'bar' not in v:
            raise ValueError('"bar" not found in a')
        return v

    class BarModel(BaseModel):
        @validator('a', check_fields=False)
        def check_a(v):
            if 'foo' not in v:
                raise ValueError('"foo" not found in a')
            return v

    model = create_model('FooModel', a='cake', __base__=BarModel, __validators__=[is_bar_in_a])
    assert model().a == 'cake'
    assert model(a='this is foobar good').a == 'this is foobar good'

    with pytest.raises(ValidationError):
        model(a='this is foo good')

    with pytest.raises(ValidationError):
        model(a='this is bar good')


def test_explicit_validators_multiple_fields():
    @validator('a', 'b')
    def check_ab(v):
        if 'foo' not in v:
            raise ValueError('"foo" not found in a')
        return v

    model = create_model('FooModel', __validators__=[check_ab], a=(str, ...), b=(str, ...))
    m = model(a='foobar', b='foobaz')
    assert m.a == 'foobar'
    assert m.b == 'foobaz'

    with pytest.raises(ValidationError):
        model(a='something else', b='foobar')

    with pytest.raises(ValidationError):
        model(a='foobar', b='something else')


def test_explicit_validators_star():
    @validator('*')
    def check_ab(v):
        if 'foo' not in v:
            raise ValueError('"foo" not found in a')
        return v

    model = create_model('FooModel', __validators__=[check_ab], a=(str, ...), b=(str, ...))
    m = model(a='foobar', b='foobaz')
    assert m.a == 'foobar'
    assert m.b == 'foobaz'

    with pytest.raises(ValidationError):
        model(a='something else', b='foobar')

    with pytest.raises(ValidationError):
        model(a='foobar', b='something else')


def test_explicit_validators_pre_whole():
    @validator('a', whole=True)
    def check_a1(v):
        v.append(456)
        return v

    @validator('a', whole=True, pre=True)
    def check_a2(v):
        v.append('123')
        return v

    model = create_model('FooModel', __validators__=[check_a1, check_a2], a=(List[int], ...))
    m = model(a=[1, 2])
    assert m.a == [1, 2, 123, 456]


def test_explicit_validators_always():
    check_calls = 0

    @validator('a', pre=True, always=True)
    def check_a(v):
        nonlocal check_calls
        check_calls += 1
        return v or 'xxx'

    model = create_model('FooModel', __validators__=[check_a], a=(str, None))
    m = model()

    assert m.a == 'xxx'
    assert check_calls == 1
    assert model(a='y').a == 'y'
    assert check_calls == 2
