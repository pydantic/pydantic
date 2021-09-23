from collections import namedtuple
from typing import Callable as TypingCallable, NamedTuple

import pytest

from pydantic.typing import Literal, is_namedtuple, is_none_type, is_typeddict

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
