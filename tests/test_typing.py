import typing
from collections import namedtuple
from typing import Callable, ClassVar, ForwardRef, NamedTuple

import pytest
from typing_extensions import Literal, get_origin

from pydantic import Field  # noqa: F401
from pydantic._internal._typing_extra import (
    NoneType,
    get_function_type_hints,
    is_classvar,
    is_literal_type,
    is_namedtuple,
    is_none_type,
    origin_is_union,
    parent_frame_namespace,
)

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


def test_is_none_type():
    assert is_none_type(Literal[None]) is True
    assert is_none_type(None) is True
    assert is_none_type(type(None)) is True
    assert is_none_type(6) is False
    assert is_none_type({}) is False
    # WARNING: It's important to test `typing.Callable` not
    # `collections.abc.Callable` (even with python >= 3.9) as they behave
    # differently
    assert is_none_type(Callable) is False


@pytest.mark.parametrize('union_gen', [lambda: typing.Union[int, str], lambda: int | str])
def test_is_union(union_gen):
    try:
        union = union_gen()
    except TypeError:
        pytest.skip('not supported in this python version')
    else:
        origin = get_origin(union)
        assert origin_is_union(origin)


def test_is_literal_with_typing_extension_literal():
    from typing_extensions import Literal

    assert is_literal_type(Literal) is False
    assert is_literal_type(Literal['foo']) is True


def test_is_literal_with_typing_literal():
    from typing import Literal

    assert is_literal_type(Literal) is False
    assert is_literal_type(Literal['foo']) is True


@pytest.mark.parametrize(
    'ann_type,extepcted',
    (
        (None, False),
        (ForwardRef('ClassVar[int]'), True),
        (ClassVar[int], True),
    ),
)
def test_is_classvar(ann_type, extepcted):
    assert is_classvar(ann_type) is extepcted


def test_parent_frame_namespace(mocker):
    assert parent_frame_namespace() is not None

    from dataclasses import dataclass

    @dataclass
    class MockedFrame:
        f_back = None

    mocker.patch('sys._getframe', return_value=MockedFrame())
    assert parent_frame_namespace() is None


def test_get_function_type_hints_none_type():
    def f(x: int, y: None) -> int:
        return x

    assert get_function_type_hints(f) == {'return': int, 'x': int, 'y': NoneType}
