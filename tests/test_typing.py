import sys
import typing
from collections import namedtuple
from typing import Annotated, Callable, ClassVar, ForwardRef, Literal, NamedTuple

import pytest
from typing_extensions import get_origin

from pydantic import BaseModel, Field  # noqa: F401
from pydantic._internal._typing_extra import (
    NoneType,
    eval_type,
    get_function_type_hints,
    is_classvar_annotation,
    is_literal,
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

ALL_TYPEDDICT_KINDS = (typing_TypedDict, typing_extensions_TypedDict)


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


@pytest.mark.parametrize(
    'union',
    [
        typing.Union[int, str],
        eval_type('int | str'),
        *([int | str] if sys.version_info >= (3, 10) else []),
    ],
)
def test_is_union(union):
    origin = get_origin(union)
    assert origin_is_union(origin)


def test_is_literal_with_typing_extension_literal():
    from typing_extensions import Literal

    assert is_literal(Literal) is False
    assert is_literal(Literal['foo']) is True


def test_is_literal_with_typing_literal():
    from typing import Literal

    assert is_literal(Literal) is False
    assert is_literal(Literal['foo']) is True


@pytest.mark.parametrize(
    ['ann_type', 'expected'],
    (
        (None, False),
        (ForwardRef('Other[int]'), False),
        (ForwardRef('Other[ClassVar[int]]'), False),
        (ForwardRef('ClassVar[int]'), True),
        (ForwardRef('t.ClassVar[int]'), True),
        (ForwardRef('typing.ClassVar[int]'), True),
        (ForwardRef('Annotated[ClassVar[int], ...]'), True),
        (ForwardRef('Annotated[t.ClassVar[int], ...]'), True),
        (ForwardRef('t.Annotated[t.ClassVar[int], ...]'), True),
        (ClassVar[int], True),
        (Annotated[ClassVar[int], ...], True),
    ),
)
def test_is_classvar_annotation(ann_type, expected):
    assert is_classvar_annotation(ann_type) is expected


def test_get_function_type_hints_none_type():
    def f(x: int, y: None) -> int:
        return x

    assert get_function_type_hints(f) == {'return': int, 'x': int, 'y': NoneType}


@pytest.mark.skipif(sys.version_info >= (3, 10), reason='testing using a feature not supported by older Python')
def test_eval_type_backport_not_installed():
    sys.modules['eval_type_backport'] = None
    try:
        with pytest.raises(TypeError) as exc_info:

            class _Model(BaseModel):
                foo: 'int | str'

        assert str(exc_info.value) == (
            "Unable to evaluate type annotation 'int | str'. If you are making use "
            'of the new typing syntax (unions using `|` since Python 3.10 or builtins subscripting '
            'since Python 3.9), you should either replace the use of new syntax with the existing '
            '`typing` constructs or install the `eval_type_backport` package.'
        )

    finally:
        del sys.modules['eval_type_backport']


def test_func_ns_excludes_default_globals() -> None:
    foo = 'foo'

    func_ns = parent_frame_namespace(parent_depth=1)
    assert func_ns is not None
    assert func_ns['foo'] == foo

    # there are more default global variables, but these are examples of well known ones
    for default_global_var in ['__name__', '__doc__', '__package__', '__builtins__']:
        assert default_global_var not in func_ns


def test_parent_frame_namespace(create_module) -> None:
    """Parent frame namespace should be `None` because we skip fetching data from the top module level."""

    @create_module
    def mod1() -> None:
        from pydantic._internal._typing_extra import parent_frame_namespace

        module_foo = 'global_foo'  # noqa: F841
        module_ns = parent_frame_namespace(parent_depth=1)  # noqa: F841
        module_ns_force = parent_frame_namespace(parent_depth=1, force=True)  # noqa: F841

    assert mod1.module_ns is None
    assert mod1.module_ns_force is not None


def test_exotic_localns() -> None:
    __foo_annotation__ = str

    class Model(BaseModel):
        foo: __foo_annotation__

    assert Model.model_fields['foo'].annotation == str
