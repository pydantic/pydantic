from inspect import signature
from typing import Any, Iterable, Union

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
        ('id: int = 1', 'bar=2', 'baz: Any', "name: str = 'John Doe'", 'foo: str', '**data'),
    )

    assert _equals(str(sig), "(id: int = 1, bar=2, *, baz: Any, name: str = 'John Doe', foo: str, **data) -> None")


def test_custom_init_signature_with_no_var_kw():
    class Model(BaseModel):
        a: float
        b: int = 2
        c: int

        def __init__(self, a: float, b: int):
            super().__init__(a=a, b=b, c=1)

        class Config:
            extra = Extra.allow

    assert _equals(str(signature(Model)), '(a: float, b: int) -> None')


def test_invalid_identifiers_signature():
    model = create_model(
        'Model', **{'123 invalid identifier!': Field(123, alias='valid_identifier'), '!': Field(0, alias='yeah')}
    )
    assert _equals(str(signature(model)), '(*, valid_identifier: int = 123, yeah: int = 0) -> None')
    model = create_model('Model', **{'123 invalid identifier!': 123, '!': Field(0, alias='yeah')})
    assert _equals(str(signature(model)), '(*, yeah: int = 0, **extra_data: Any) -> None')


def test_use_field_name():
    class Foo(BaseModel):
        foo: str = Field(..., alias='this is invalid')

        class Config:
            allow_population_by_field_name = True

    assert _equals(str(signature(Foo)), '(*, foo: str) -> None')


def test_extra_allow_no_conflict():
    class Model(BaseModel):
        spam: str

        class Config:
            extra = Extra.allow

    assert _equals(str(signature(Model)), '(*, spam: str, **extra_data: Any) -> None')


def test_extra_allow_conflict():
    class Model(BaseModel):
        extra_data: str

        class Config:
            extra = Extra.allow

    assert _equals(str(signature(Model)), '(*, extra_data: str, **extra_data_: Any) -> None')


def test_extra_allow_conflict_twice():
    class Model(BaseModel):
        extra_data: str
        extra_data_: str

        class Config:
            extra = Extra.allow

    assert _equals(str(signature(Model)), '(*, extra_data: str, extra_data_: str, **extra_data__: Any) -> None')


def test_extra_allow_conflict_custom_signature():
    class Model(BaseModel):
        extra_data: int

        def __init__(self, extra_data: int = 1, **foobar: Any):
            super().__init__(extra_data=extra_data, **foobar)

        class Config:
            extra = Extra.allow

    assert _equals(str(signature(Model)), '(extra_data: int = 1, **foobar: Any) -> None')


def test_signature_is_class_only():
    class Model(BaseModel):
        foo: int = 123

        def __call__(self, a: int) -> bool:
            pass

    assert _equals(str(signature(Model)), '(*, foo: int = 123) -> None')
    assert _equals(str(signature(Model())), '(a: int) -> bool')
    assert not hasattr(Model(), '__signature__')
