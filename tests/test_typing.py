import sys
from collections import namedtuple
from typing import Any, Callable as TypingCallable, Dict, ForwardRef, List, NamedTuple, NewType, Union  # noqa: F401

import pytest
from typing_extensions import Annotated  # noqa: F401

from pydantic import Field  # noqa: F401
from pydantic.typing import Literal, convert_generics, is_literal_type, is_namedtuple, is_none_type, is_typeddict

try:
    from typing import TypedDict as typing_TypedDict
except ImportError:
    typing_TypedDict = None

try:
    from typing_extensions import TypedDict as typing_extensions_TypedDict
except ImportError:
    typing_extensions_TypedDict = None


try:
    from mypy_extensions import TypedDict as mypy_extensions_TypedDict
except ImportError:
    mypy_extensions_TypedDict = None

ALL_TYPEDDICT_KINDS = (typing_TypedDict, typing_extensions_TypedDict, mypy_extensions_TypedDict)


def test_is_namedtuple():
    class Employee(NamedTuple):
        name: str
        id: int = 3

    assert is_namedtuple(namedtuple('Point', 'x y')) is True
    assert is_namedtuple(Employee) is True
    assert is_namedtuple(NamedTuple('Employee', [('name', str), ('id', int)])) is True

    class Other(tuple):
        name: str
        id: int

    assert is_namedtuple(Other) is False


@pytest.mark.parametrize('TypedDict', (t for t in ALL_TYPEDDICT_KINDS if t is not None))
def test_is_typeddict_typing(TypedDict):
    class Employee(TypedDict):
        name: str
        id: int

    assert is_typeddict(Employee) is True
    assert is_typeddict(TypedDict('Employee', {'name': str, 'id': int})) is True

    class Other(dict):
        name: str
        id: int

    assert is_typeddict(Other) is False


def test_is_none_type():
    assert is_none_type(Literal[None]) is True
    assert is_none_type(None) is True
    assert is_none_type(type(None)) is True
    assert is_none_type(6) is False
    assert is_none_type({}) is False
    # WARNING: It's important to test `typing.Callable` not
    # `collections.abc.Callable` (even with python >= 3.9) as they behave
    # differently
    assert is_none_type(TypingCallable) is False


class Hero:
    pass


class Team:
    pass


@pytest.mark.skipif(sys.version_info < (3, 9), reason='PEP585 generics only supported for python 3.9 and above.')
@pytest.mark.parametrize(
    ['type_', 'expectations'],
    [
        ('int', 'int'),
        ('Union[list["Hero"], int]', 'Union[list[ForwardRef("Hero")], int]'),
        ('list["Hero"]', 'list[ForwardRef("Hero")]'),
        ('dict["Hero", "Team"]', 'dict[ForwardRef("Hero"), ForwardRef("Team")]'),
        ('dict["Hero", list["Team"]]', 'dict[ForwardRef("Hero"), list[ForwardRef("Team")]]'),
        ('dict["Hero", List["Team"]]', 'dict[ForwardRef("Hero"), List[ForwardRef("Team")]]'),
        ('Dict["Hero", list["Team"]]', 'Dict[ForwardRef("Hero"), list[ForwardRef("Team")]]'),
        (
            'Annotated[list["Hero"], Field(min_length=2)]',
            'Annotated[list[ForwardRef("Hero")], Field(min_length=2)]',
        ),
    ],
)
def test_convert_generics(type_, expectations):
    assert str(convert_generics(eval(type_))) == str(eval(expectations))


@pytest.mark.skipif(sys.version_info < (3, 10), reason='NewType class was added in python 3.10.')
def test_convert_generics_unsettable_args():
    class User(NewType):

        __origin__ = type(list[str])
        __args__ = (list['Hero'],)

        def __init__(self, name: str, tp: type) -> None:
            super().__init__(name, tp)

        def __setattr__(self, __name: str, __value: Any) -> None:
            if __name == '__args__':
                raise AttributeError  # will be thrown during the generics conversion
            return super().__setattr__(__name, __value)

    # tests that convert_generics will not throw an exception even if __args__ isn't settable
    assert convert_generics(User('MyUser', str)).__args__ == (list['Hero'],)


@pytest.mark.skipif(sys.version_info < (3, 10), reason='PEP604 unions only supported for python 3.10 and above.')
def test_convert_generics_pep604():
    assert (
        convert_generics(dict['Hero', list['Team']] | int) == dict[ForwardRef('Hero'), list[ForwardRef('Team')]] | int
    )


def test_is_literal_with_typing_extension_literal():
    from typing_extensions import Literal

    assert is_literal_type(Literal) is False
    assert is_literal_type(Literal['foo']) is True


@pytest.mark.skipif(sys.version_info < (3, 8), reason='`typing.Literal` is available for python 3.8 and above.')
def test_is_literal_with_typing_literal():
    from typing import Literal

    assert is_literal_type(Literal) is False
    assert is_literal_type(Literal['foo']) is True
