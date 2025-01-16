from typing import Annotated

import pytest
from annotated_types import Ge
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError

from .conftest import Err


@pytest.mark.parametrize(
    'mode,value,expected',
    [
        ('python', {'a': 1, 'b': 'b', 'c': (3, '4')}, {'a': 1, 'b': 'b', 'c': (3, '4')}),
        ('python', {'a': 1, 'b': 'b', 'c': (3,)}, {'a': 1, 'b': 'b'}),
        ('python', {'a': 1, 'b': 'b'}, {'a': 1, 'b': 'b'}),
        ('json', '{"a": 1, "b": "b", "c": [3, "4"]}', {'a': 1, 'b': 'b', 'c': (3, '4')}),
        ('json', '{"a": 1, "b": "b", "c": [3, "4"]}', {'a': 1, 'b': 'b', 'c': (3, '4')}),
        ('json', '{"a": 1, "b": "b", "c": [3]}', {'a': 1, 'b': 'b'}),
        ('json', '{"a": 1, "b": "b", "c": [3', {'a': 1, 'b': 'b'}),
        ('json', '{"a": 1, "b": "b', {'a': 1}),
        ('json', '{"a": 1, "b": ', {'a': 1}),
        ('python', {'a': 1, 'c': (3,), 'b': 'b'}, Err(r'c\.1\s+Field required')),
        ('json', '{"a": 1, "c": [3], "b": "b"}', Err(r'c\.1\s+Field required')),
    ],
)
def test_typed_dict(mode, value, expected):
    class Foobar(TypedDict, total=False):
        a: int
        b: str
        c: tuple[int, str]

    ta = TypeAdapter(Foobar)
    if mode == 'python':
        if isinstance(expected, Err):
            with pytest.raises(ValidationError, match=expected.message):
                ta.validate_python(value, experimental_allow_partial=True)
        else:
            assert ta.validate_python(value, experimental_allow_partial=True) == expected
    else:
        if isinstance(expected, Err):
            with pytest.raises(ValidationError, match=expected.message):
                ta.validate_json(value, experimental_allow_partial=True)
        else:
            assert ta.validate_json(value, experimental_allow_partial=True) == expected


@pytest.mark.parametrize(
    'mode,value,expected',
    [
        ('python', [10, 20, 30], [10, 20, 30]),
        ('python', ['10', '20', '30'], [10, 20, 30]),
        ('python', [10, 20, 30], [10, 20, 30]),
        ('python', [10, 20, 3], [10, 20]),
        ('json', '[10, 20, 30]', [10, 20, 30]),
        ('json', '[10, 20, 30', [10, 20, 30]),
        ('json', '[10, 20, 3', [10, 20]),
    ],
)
def test_list(mode, value, expected):
    ta = TypeAdapter(list[Annotated[int, Ge(10)]])
    if mode == 'python':
        if isinstance(expected, Err):
            with pytest.raises(ValidationError, match=expected.message):
                ta.validate_python(value, experimental_allow_partial=True)
        else:
            assert ta.validate_python(value, experimental_allow_partial=True) == expected
    else:
        if isinstance(expected, Err):
            with pytest.raises(ValidationError, match=expected.message):
                ta.validate_json(value, experimental_allow_partial=True)
        else:
            assert ta.validate_json(value, experimental_allow_partial=True) == expected


def test_dict():
    ta = TypeAdapter(dict[str, Annotated[int, Ge(10)]])
    eap = dict(experimental_allow_partial=True)

    assert ta.validate_python({'a': 10, 'b': 20, 'c': 30}, **eap) == {'a': 10, 'b': 20, 'c': 30}
    assert ta.validate_python({'a': 10, 'b': 20, 'c': 3}, **eap) == {'a': 10, 'b': 20}
    assert ta.validate_strings({'a': '10', 'b': '20', 'c': '30'}, strict=True, **eap) == {'a': 10, 'b': 20, 'c': 30}
    assert ta.validate_strings({'a': '10', 'b': '20', 'c': '3'}, strict=True, **eap) == {'a': 10, 'b': 20}
    assert ta.validate_json('{"a": 10, "b": 20, "c": 30}', **eap) == {'a': 10, 'b': 20, 'c': 30}
    assert ta.validate_json('{"a": 10, "b": 20, "c": 3', **eap) == {'a': 10, 'b': 20}
    assert ta.validate_json('{"a": 10, "b": 20, "c": 3}', **eap) == {'a': 10, 'b': 20}
