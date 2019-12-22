from inspect import signature
from typing import Any, Union, Iterable

from pydantic import BaseModel, Extra, Field, create_model


def _equals(a: Union[str, Iterable[str]], b: Union[str, Iterable[str]]) -> bool:
    """
    compare strings with spaces removed
    """
    if isinstance(a, str) and isinstance(b, str):
        return a.replace(' ', '') == b.replace(' ', '')
    elif isinstance(a, Iterable) and isinstance(b, Iterable):
        return all(_equals(a_, b_) for a_, b_ in zip(a, b))
    else:
        raise TypeError(f'arguments must be both strings or both lists, not {type(a)}, {type(b)}')


def test_model_signature():
    class Model(BaseModel):
        a: float = Field(..., title='A')
        b = Field(10)

    sig = signature(Model)
    assert sig != signature(BaseModel)
    assert _equals(map(str, sig.parameters.values()), ('a: float', 'b: int = 10'))
    assert _equals(str(sig), '(*, a: float, b: int = 10) -> None')


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
    assert _equals(
        map(str, sig.parameters.values()),
        ('id: int = 1', 'bar=2', 'baz: Any', "name: str = 'John Doe'", 'foo: str', '**data')
    )

    assert _equals(
        str(sig),
        "(id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', foo: str, **data) -> None"
    )


def test_invalid_identifiers_signature():
    model = create_model(
        'Model', **{'123 invalid identifier!': Field(123, alias='valid_identifier'), '!': Field(0, alias='yeah')}
    )
    assert _equals(
        str(signature(model)),
        '(*, valid_identifier: int = 123, yeah: int = 0) -> None'
    )
    model = create_model('Model', **{'123 invalid identifier!': 123, '!': Field(0, alias='yeah')})
    assert _equals(
        str(signature(model)),
        '(*, yeah: int = 0, **data: Any) -> None'
    )
