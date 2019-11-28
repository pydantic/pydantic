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

    assert [str(p) for p in sig.parameters.values()] == ['__pydantic_self__', 'a: float', 'b: int = 10', '**data: Any']

    assert Model.__init__.__name__ == '__init__'
    assert Model.__init__.__module__ == 'pydantic.main'

    expected_signature = '(__pydantic_self__, *, a: float, b: int = 10, **data: Any) -> None'
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')
    assert Model.__init__.__doc__.replace(' ', '').replace('\n', '') == (
        'Signature is generated based on model fields. Real signature:'
        '(__pydantic_self__, **data: Any) -> None'
        'Create a new model by parsing and validating input data from keyword arguments'
        ':raises ValidationError if the input data cannot be parsed to for a valid model.'
    ).replace(' ', '').replace('\n', '')


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
    assert [str(p) for p in sig.parameters.values()] == [
        'self',
        'id: int = 1',
        'bar=2',
        'baz: Any',
        "name: str = 'John Doe'",
        '**data',
    ]

    expected_signature = "(self, id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', **data)"
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')
    assert MyModel.__init__.__doc__.replace(' ', '').replace('\n', '') == (
        'Signature is generated based on model fields. Real signature:'
        '(self, id: int = 1, bar=2, *, baz: Any, **data)'
    ).replace(' ', '').replace('\n', '')

    assert MyModel.__init__.__name__ == '__init__'
    assert MyModel.__init__.__module__ == test_custom_init_signature.__module__


@pytest.mark.skipif(not compiled, reason='if not compiled, __init__ is copied without need to reference to original')
def test_original_init_compiled():
    assert hasattr(BaseModel.__init__, '__origin_init__')
    base_model_origin_init = BaseModel.__init__.__origin_init__
    assert base_model_origin_init is not BaseModel.__init__

    class Model(BaseModel):
        id: int

    assert Model.__init__.__origin_init__ is base_model_origin_init

    class ModelTwo(BaseModel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        origin = __init__

    assert ModelTwo.__init__ is not ModelTwo.origin
    assert ModelTwo.__init__.__origin_init__ is ModelTwo.origin
    assert ModelTwo.__init__.__origin_init__ is not base_model_origin_init


@pytest.mark.skipif(compiled, reason='for the reason above, this test cannot be run when compiled')
def test_original_init_not_compiled():
    assert not hasattr(BaseModel.__init__, '__origin__')

    class Model(BaseModel):
        id: int

    assert Model.__init__ is not BaseModel.__init__
    assert Model.__init__.__code__ == BaseModel.__init__.__code__
