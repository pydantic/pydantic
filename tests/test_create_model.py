import pytest

from pydantic import BaseModel, ConfigError, ValidationError, create_model


def test_create_model():
    model = create_model('FooModel', foo=(str, ...), bar=123)
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
    with pytest.raises(ConfigError):
        create_model('FooModel', _foo=(str, ...))


def test_field_wrong_tuple():
    with pytest.raises(ConfigError):
        create_model('FooModel', foo=(1, 2, 3))


def test_create_model_inheritance():
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
