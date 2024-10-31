import pytest
from annotated_types import Ge
from typing_extensions import Annotated, TypedDict

from pydantic import TypeAdapter, ValidationError


def test_typed_dict():
    class Foobar(TypedDict, total=False):
        a: int
        b: str
        c: tuple[int, str]

    ta = TypeAdapter(Foobar)
    eap = dict(experimental_allow_partial=True)

    assert ta.validate_python({'a': 1, 'b': 'b', 'c': (3, '4')}) == {'a': 1, 'b': 'b', 'c': (3, '4')}
    assert ta.validate_python({'a': 1, 'b': 'b', 'c': (3, '4')}, **eap) == {'a': 1, 'b': 'b', 'c': (3, '4')}
    assert ta.validate_python({'a': 1, 'b': 'b', 'c': (3,)}, **eap) == {'a': 1, 'b': 'b'}
    assert ta.validate_python({'a': 1, 'b': 'b'}, **eap) == {'a': 1, 'b': 'b'}
    assert ta.validate_json('{"a": 1, "b": "b", "c": [3, "4"]}') == {'a': 1, 'b': 'b', 'c': (3, '4')}
    assert ta.validate_json('{"a": 1, "b": "b", "c": [3, "4"]}', **eap) == {'a': 1, 'b': 'b', 'c': (3, '4')}
    assert ta.validate_json('{"a": 1, "b": "b", "c": [3]}', **eap) == {'a': 1, 'b': 'b'}
    assert ta.validate_json('{"a": 1, "b": "b", "c": [3', **eap) == {'a': 1, 'b': 'b'}
    assert ta.validate_json('{"a": 1, "b": "b', **eap) == {'a': 1, 'b': 'b'}
    assert ta.validate_json('{"a": 1, "b": ', **eap) == {'a': 1}
    with pytest.raises(ValidationError, match=r'c\.1\s+Field required'):
        ta.validate_python({'a': 1, 'c': (3,), 'b': 'b'}, **eap)
    with pytest.raises(ValidationError, match=r'c\.1\s+Field required'):
        ta.validate_json('{"a": 1, "c": [3], "b": "b"}', **eap)


def test_list():
    ta = TypeAdapter(list[Annotated[int, Ge(10)]])
    eap = dict(experimental_allow_partial=True)

    assert ta.validate_python([10, 20, 30]) == [10, 20, 30]
    assert ta.validate_python(['10', '20', '30']) == [10, 20, 30]
    assert ta.validate_python([10, 20, 30], **eap) == [10, 20, 30]
    assert ta.validate_python([10, 20, 3], **eap) == [10, 20]
    assert ta.validate_json('[10, 20, 30]') == [10, 20, 30]
    assert ta.validate_json('[10, 20, 30', **eap) == [10, 20, 30]
    assert ta.validate_json('[10, 20, 3', **eap) == [10, 20]


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
