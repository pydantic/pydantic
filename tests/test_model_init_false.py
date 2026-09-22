import pytest

from pydantic import BaseModel, Field, ValidationError


def test_init_false_is_absent_from_init_and_settable_after() -> None:
    class Model(BaseModel):
        a: int
        b: str = ''
        c: int = Field(default=1, init=False)

    assert 'c' not in Model.__signature__.parameters

    model = Model(a=1)
    assert model.c == 1
    model.c = 5
    assert model.c == 5

    with pytest.raises(TypeError, match="unexpected keyword argument 'c'"):
        Model(a=1, c=2)


def test_init_defaults_to_true() -> None:
    class Model(BaseModel):
        a: int = Field(default=1)

    assert 'a' in Model.__signature__.parameters
    assert Model().a == 1
    assert Model(a=3).a == 3


def test_init_false_default_factory_and_subclass() -> None:
    class Parent(BaseModel):
        a: int
        c: list[int] = Field(default_factory=list, init=False)

    class Child(Parent):
        b: str = ''

    child = Child(a=1, b='x')
    assert child.c == []
    child.c.append(4)
    assert child.c == [4]
    assert 'c' not in Child.__signature__.parameters

    with pytest.raises(ValidationError):
        Parent()
