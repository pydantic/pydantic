import collections.abc
import os
import pickle
import time
from collections.abc import Callable
from copy import copy, deepcopy
from typing import Annotated, Generic, TypeVar, Union

import pytest
from pydantic_core import PydanticCustomError, PydanticUndefined

from pydantic import BaseModel
from pydantic._internal import _repr
from pydantic._internal._typing_extra import get_origin
from pydantic._internal._utils import (
    BUILTIN_COLLECTIONS,
    LazyClassAttribute,
    all_identical,
    lenient_issubclass,
    smart_deepcopy,
)
from pydantic._internal._validators import import_string
from pydantic.alias_generators import to_camel, to_pascal, to_snake

try:
    import devtools
except ImportError:
    devtools = None


def test_import_module():
    assert import_string('os.path') == os.path


def test_import_module_invalid():
    with pytest.raises(PydanticCustomError, match="Invalid python path: No module named 'xx'"):
        import_string('xx')


def test_import_no_attr():
    with pytest.raises(PydanticCustomError, match="cannot import name 'foobar' from 'os'"):
        import_string('os:foobar')


def foobar(a, b, c=4):
    pass


T = TypeVar('T')


class LoggedVar(Generic[T]):
    def get(self) -> T: ...


@pytest.mark.parametrize(
    'value,expected',
    [
        (str, 'str'),
        ('foobar', 'str'),
        ('SomeForwardRefString', 'str'),  # included to document current behavior; could be changed
        pytest.param(Union[str, int], 'Union[str, int]', id='Union[str, int]'),  # noqa: UP007  # TODO remove when we drop support for Python 3.13
        pytest.param(str | int, 'Union[str, int]', id='str | int'),
        (list, 'list'),
        (list[int], 'list[int]'),
        ([1, 2, 3], 'list'),
        (list[dict[str, int]], 'list[dict[str, int]]'),
        (tuple[str, int, float], 'tuple[str, int, float]'),
        (tuple[str, ...], 'tuple[str, ...]'),
        (Union[int, list[str], tuple[str, int]], 'Union[int, list[str], tuple[str, int]]'),  # noqa: UP007
        (foobar, 'foobar'),
        (time.time_ns, 'time_ns'),
        (LoggedVar, 'LoggedVar'),
        (LoggedVar(), 'LoggedVar'),
        (LoggedVar[int], 'LoggedVar[int]'),
        (LoggedVar[dict[int, str]], 'LoggedVar[dict[int, str]]'),
    ],
)
def test_display_as_type(value, expected):
    assert _repr.display_as_type(value) == expected


def test_lenient_issubclass():
    class A(str):
        pass

    assert lenient_issubclass(A, str) is True


def test_lenient_issubclass_with_generic_aliases():
    from collections.abc import Mapping

    # should not raise an error here:
    assert lenient_issubclass(list[str], Mapping) is False


def test_lenient_issubclass_is_lenient():
    assert lenient_issubclass('a', 'a') is False


def test_pretty():
    class MyTestModel(BaseModel):
        a: int = 1
        b: list[int] = [1, 2, 3]

    m = MyTestModel()
    assert m.__repr_name__() == 'MyTestModel'
    assert str(m) == 'a=1 b=[1, 2, 3]'
    assert repr(m) == 'MyTestModel(a=1, b=[1, 2, 3])'
    assert list(m.__pretty__(lambda x: f'fmt: {x!r}')) == [
        'MyTestModel(',
        1,
        'a=',
        'fmt: 1',
        ',',
        0,
        'b=',
        'fmt: [1, 2, 3]',
        ',',
        0,
        -1,
        ')',
    ]


@pytest.mark.skipif(not devtools, reason='devtools not installed')
def test_devtools_output():
    class MyTestModel(BaseModel):
        a: int = 1
        b: list[int] = [1, 2, 3]

    assert devtools.pformat(MyTestModel()) == 'MyTestModel(\n    a=1,\n    b=[1, 2, 3],\n)'


def test_undefined_repr():
    assert repr(PydanticUndefined) == 'PydanticUndefined'


def test_undefined_copy():
    assert copy(PydanticUndefined) is PydanticUndefined
    assert deepcopy(PydanticUndefined) is PydanticUndefined


def test_class_attribute():
    class Foo:
        attr = LazyClassAttribute('attr', lambda: 'foo')

    assert Foo.attr == 'foo'

    with pytest.raises(AttributeError, match="'attr' attribute of 'Foo' is class-only"):
        Foo().attr

    f = Foo()
    f.attr = 'not foo'
    assert f.attr == 'not foo'


@pytest.mark.parametrize(
    'obj',
    (
        pytest.param(1, id='int-1'),
        pytest.param(1.0, id='float-1.0'),
        pytest.param('1', id='str-1'),
        pytest.param(b'1', id='bytes-1'),
        int,
        None,
        test_class_attribute,
        len,
        test_class_attribute.__code__,
        lambda: ...,
        ...,
    ),
)
def test_smart_deepcopy_immutable_non_sequence(obj, mocker):
    # make sure deepcopy is not used
    # (other option will be to use obj.copy(), but this will produce error as none of given objects have this method)
    mocker.patch('pydantic._internal._utils.deepcopy', side_effect=RuntimeError)
    assert smart_deepcopy(obj) is deepcopy(obj) is obj


@pytest.mark.parametrize('empty_collection', [collection() for collection in BUILTIN_COLLECTIONS])
def test_smart_deepcopy_empty_collection(empty_collection, mocker):
    mocker.patch('pydantic._internal._utils.deepcopy', side_effect=RuntimeError)  # make sure deepcopy is not used
    if not isinstance(empty_collection, (tuple, frozenset)):  # empty tuple or frozenset are always the same object
        assert smart_deepcopy(empty_collection) is not empty_collection


@pytest.mark.thread_unsafe(reason='Monkeypatching')
@pytest.mark.parametrize(
    'collection', [c.fromkeys((1,)) if issubclass(c, dict) else c((1,)) for c in BUILTIN_COLLECTIONS]
)
def test_smart_deepcopy_collection(collection, mocker):
    expected_value = object()
    mocker.patch('pydantic._internal._utils.deepcopy', return_value=expected_value)
    assert smart_deepcopy(collection) is expected_value


@pytest.mark.parametrize('error', [TypeError, ValueError, RuntimeError])
def test_smart_deepcopy_error(error, mocker):
    class RaiseOnBooleanOperation(str):
        def __bool__(self):
            raise error('raised error')

    obj = RaiseOnBooleanOperation()
    expected_value = deepcopy(obj)
    assert smart_deepcopy(obj) == expected_value


T = TypeVar('T')


@pytest.mark.parametrize(
    'input_value,output_value',
    [
        (Annotated[int, 10] if Annotated else None, Annotated),
        (Callable[[], T][int], collections.abc.Callable),
        (dict[str, int], dict),
        (list[str], list),
        (Union[int, str], Union),  # noqa: UP007
        (int, None),
    ],
)
def test_get_origin(input_value, output_value):
    if input_value is None:
        pytest.skip('Skipping undefined hint for this python version')
    assert get_origin(input_value) is output_value


def test_all_identical():
    a, b = object(), object()
    c = [b]
    assert all_identical([a, b], [a, b]) is True
    assert all_identical([a, b], [a, b]) is True
    assert all_identical([a, b, b], [a, b, b]) is True
    assert all_identical([a, c, b], [a, c, b]) is True

    assert all_identical([], [a]) is False, 'Expected iterables with different lengths to evaluate to `False`'
    assert all_identical([a], []) is False, 'Expected iterables with different lengths to evaluate to `False`'
    assert all_identical([a, [b], b], [a, [b], b]) is False, (
        'New list objects are different objects and should therefore not be identical.'
    )


def test_undefined_pickle():
    undefined2 = pickle.loads(pickle.dumps(PydanticUndefined))
    assert undefined2 is PydanticUndefined


def test_on_lower_camel_zero_length():
    assert to_camel('') == ''


def test_on_lower_camel_one_length():
    assert to_camel('a') == 'a'


def test_on_lower_camel_many_length():
    assert to_camel('i_like_turtles') == 'iLikeTurtles'


@pytest.mark.parametrize(
    'value,result',
    [
        ('snake_to_camel', 'snakeToCamel'),
        ('snake_2_camel', 'snake2Camel'),
        ('snake2camel', 'snake2Camel'),
        ('_snake_to_camel', '_snakeToCamel'),
        ('snake_to_camel_', 'snakeToCamel_'),
        ('__snake_to_camel__', '__snakeToCamel__'),
        ('snake_2', 'snake2'),
        ('_snake_2', '_snake2'),
        ('snake_2_', 'snake2_'),
    ],
)
def test_snake2camel_start_lower(value: str, result: str) -> None:
    assert to_camel(value) == result


@pytest.mark.parametrize(
    'value,result',
    [
        ('snake_to_camel', 'SnakeToCamel'),
        ('snake_2_camel', 'Snake2Camel'),
        ('snake2camel', 'Snake2Camel'),
        ('_snake_to_camel', '_SnakeToCamel'),
        ('snake_to_camel_', 'SnakeToCamel_'),
        ('__snake_to_camel__', '__SnakeToCamel__'),
        ('snake_2', 'Snake2'),
        ('_snake_2', '_Snake2'),
        ('snake_2_', 'Snake2_'),
    ],
)
def test_snake2pascal(value: str, result: str) -> None:
    assert to_pascal(value) == result


@pytest.mark.parametrize(
    'value,result',
    [
        ('camel_to_snake', 'camel_to_snake'),
        ('camelToSnake', 'camel_to_snake'),
        ('camel2Snake', 'camel_2_snake'),
        ('_camelToSnake', '_camel_to_snake'),
        ('camelToSnake_', 'camel_to_snake_'),
        ('__camelToSnake__', '__camel_to_snake__'),
        ('CamelToSnake', 'camel_to_snake'),
        ('Camel2Snake', 'camel_2_snake'),
        ('_CamelToSnake', '_camel_to_snake'),
        ('CamelToSnake_', 'camel_to_snake_'),
        ('CAMELToSnake', 'camel_to_snake'),
        ('__CamelToSnake__', '__camel_to_snake__'),
        ('Camel2', 'camel_2'),
        ('Camel2_', 'camel_2_'),
        ('_Camel2', '_camel_2'),
        ('camel2', 'camel_2'),
        ('camel2_', 'camel_2_'),
        ('_camel2', '_camel_2'),
        ('kebab-to-snake', 'kebab_to_snake'),
        ('kebab-Snake', 'kebab_snake'),
        ('Kebab-Snake', 'kebab_snake'),
        ('PascalToSnake', 'pascal_to_snake'),
        ('snake_to_snake', 'snake_to_snake'),
        ('snakeV2', 'snake_v2'),
    ],
)
def test_to_snake(value: str, result: str) -> None:
    assert to_snake(value) == result


def test_to_camel_from_camel() -> None:
    assert to_camel('alreadyCamel') == 'alreadyCamel'
