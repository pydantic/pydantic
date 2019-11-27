from inspect import Parameter, signature
from typing import Any

import pytest

from pydantic import BaseModel, Extra, compiled

pos_or_kw = Parameter.POSITIONAL_OR_KEYWORD
kw_only = Parameter.KEYWORD_ONLY
empty = Parameter.empty


def test_init_signature():
    class Model(BaseModel):
        a: float
        b: int = 10

    assert BaseModel.__init__ is not Model.__init__
    sig = signature(Model.__init__)
    assert sig != signature(BaseModel.__init__)

    expected_signature = '(__pydantic_self__, *, a: float, b: int = 10, **data: Any) -> None'
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')
    assert Model.__init__.__doc__.replace(' ', '').replace('\n', '') == (
        'Signature is generated based on model fields. Real signature:'
        '(__pydantic_self__, **data: Any) -> None'
        'Create a new model by parsing and validating input data from keyword arguments'
        ':raises ValidationError if the input data cannot be parsed to for a valid model.'
    ).replace(' ', '').replace('\n', '')

    params = sig.parameters
    params_iterator = iter(sig.parameters.values())  # checking order
    for name, kind, annotation, default in (
        ('__pydantic_self__', pos_or_kw, empty, empty),
        ('a', kw_only, int, empty),
        ('b', kw_only, float, 10),
    ):
        assert name in params
        param: Parameter = params[name]
        assert next(params_iterator) is param
        assert param.kind is kind
        assert param.default == default

    assert Model.__init__.__qualname__ == 'BaseModel.__init__'
    assert Model.__init__.__module__ == 'pydantic.main'


def test_custom_init_signature():
    class MyModel(BaseModel):
        id: int
        name: str = 'John Doe'

        class Config:
            extra = Extra.allow

        def __init__(self, id: int = 1, bar=2, *, baz: Any, **data):
            super().__init__(id=id, **data)
            self.bar = bar
            self.baz = baz

    m = MyModel(foo=2, id=1, baz='Ok!')
    assert m.id == 1
    assert m.bar == 2
    assert m.baz == 'Ok!'
    assert m.name == 'John Doe'

    sig = signature(MyModel.__init__)
    params = sig.parameters
    params_iterator = iter(params.values())
    for name, kind, annotation, default in (
        ('self', pos_or_kw, empty, empty),
        ('id', pos_or_kw, int, 1),
        ('bar', pos_or_kw, empty, 2),
        ('baz', kw_only, Any, empty),
        ('name', kw_only, str, 'John Doe'),
    ):
        assert name in params
        param: Parameter = params[name]
        assert param is next(params_iterator)
        assert param.kind is kind
        assert param.default == default

    expected_signature = "(self, id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', **data)"
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')
    assert MyModel.__init__.__doc__.replace(' ', '').replace('\n', '') == (
        'Signature is generated based on model fields. Real signature:'
        '(self, id: int = 1, bar=2, *, baz: Any, **data)'
    ).replace(' ', '').replace('\n', '')
    assert MyModel.__init__.__qualname__ == test_custom_init_signature.__name__ + '.<locals>.MyModel.__init__'
    assert MyModel.__init__.__module__ == test_custom_init_signature.__module__


@pytest.mark.skipif(not compiled, reason='if not compiled, __init__ is copied without need to reference to original')
def test_original_init_compiled():
    assert hasattr(BaseModel.__init__, '__origin__')
    base_model_origin_init = BaseModel.__init__.__origin__
    assert base_model_origin_init is not BaseModel.__init__

    class Model(BaseModel):
        id: int

    assert Model.__init__.__origin__ == base_model_origin_init

    class ModelTwo(BaseModel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        origin = __init__

    assert ModelTwo.__init__ is not ModelTwo.origin
    assert ModelTwo.__init__.__origin__ is ModelTwo.origin
    assert ModelTwo.__init__.__origin__ is not base_model_origin_init


@pytest.mark.skipif(compiled, reason='for the reason above, this test cannot be runned when compiled')
def test_original_init_not_compiled():
    assert not hasattr(BaseModel.__init__, '__origin__')

    class Model(BaseModel):
        id: int

    assert Model.__init__ is not BaseModel.__init__
    assert Model.__init__.__code__ == BaseModel.__init__.__code__
