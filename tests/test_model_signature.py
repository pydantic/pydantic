from inspect import signature
from typing import Any

from pydantic import BaseModel, Extra, Field, create_model


def test_model_signature():
    class Model(BaseModel):
        a: float = Field(..., title='A')
        b = Field(10)

    sig = signature(Model)
    assert sig != signature(BaseModel)

    assert [str(p).replace(' ', '') for p in sig.parameters.values()] == [
        arg.replace(' ', '') for arg in ('a: float', 'b: int = 10')
    ]

    expected_signature = '(*, a: float, b: int = 10) -> None'
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')


def test_custom_init_signature():
    class MyModel(BaseModel):
        id: int
        name: str = 'John Doe'
        f__: str = Field(..., alias='foo')

        class Config:
            extra = Extra.allow

        def __init__(self, id: int = 1, bar=2, *, baz: Any, **data):
            super().__init__(id=id, **data)
            self.bar = bar
            self.baz = baz

    sig = signature(MyModel)
    assert [str(p).replace(' ', '') for p in sig.parameters.values()] == [
        arg.replace(' ', '')
        for arg in ('id: int = 1', 'bar=2', 'baz: Any', "name: str = 'John Doe'", 'foo: str', '**data')
    ]

    expected_signature = "(id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', foo: str, **data) -> None"
    assert str(sig).replace(' ', '') == expected_signature.replace(' ', '')


def test_invalid_identifiers_signature():
    model = create_model(
        'Model', **{'123 invalid identifier!': Field(123, alias='valid_identifier'), '!': Field(0, alias='yeah')}
    )
    assert str(signature(model)).replace(' ', '') == (
        '(*, valid_identifier: int = 123, yeah: int = 0) -> None'.replace(' ', '')
    )
    model = create_model('Model', **{'123 invalid identifier!': 123, '!': Field(0, alias='yeah')})
    assert str(signature(model)).replace(' ', '') == '(*, yeah: int = 0, **data: Any) -> None'.replace(' ', '')
