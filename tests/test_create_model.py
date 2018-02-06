import pytest

from pydantic import BaseModel, ConfigError, ValidationError, create_model, validator


def test_create_model():
    model = create_model('FooModel', foo=(str, ...), bar=123)
    assert issubclass(model, BaseModel)
    assert issubclass(model.config, BaseModel.Config)
    assert model.__name__ == 'FooModel'
    assert model.__fields__.keys() == {'foo', 'bar'}
    assert model.__validators__ == {}
    assert model.config.__name__ == 'BaseConfig'


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
    with pytest.raises(ConfigError):
        create_model('FooModel', foo=(1, 2, 3))


def test_config_and_base():
    with pytest.raises(ConfigError):
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
    class Config(BaseModel.Config):
        fields = {
            'foo': 'api-foo-field'
        }
    model = create_model('FooModel', foo=(int, ...), __config__=Config)
    assert model(**{'api-foo-field': '987'}).foo == 987
    with pytest.raises(ValidationError):
        model(foo=654)


def test_inheritance_validators():
    class BarModel(BaseModel):
        @validator('a')
        def check_a(cls, v):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    model = create_model('FooModel', a='cake', __base__=BarModel)
    assert model().a == 'cake'
    with pytest.raises(ValidationError):
        model(a='something else')
