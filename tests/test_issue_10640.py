"""
Test for issue #10640: model_validate_json confusing exception with union types

This test verifies that model_validate_json correctly handles union types
like str | Iterable[T] and selects the str branch when the JSON value is a string.
"""

import json
from typing import Iterable

from pydantic import BaseModel
from typing_extensions import Required, TypedDict


class Inner(TypedDict):
    msg: Required[str]


class Outer(BaseModel):
    content: str | Iterable[Inner]


def force(x):
    """Force validation if x is a lazy ValidationIterator."""
    if isinstance(x, str):
        return x
    return list(x)


def test_model_validate_json_string_union():
    """Test that model_validate_json correctly validates string in str | Iterable union"""
    model = Outer(content="Hello")

    json_text = model.model_dump_json()
    assert json_text == '{"content":"Hello"}'

    # model_validate(json.loads(...)) should work
    obj = Outer.model_validate(json.loads(json_text))
    obj.content = force(obj.content)
    assert obj.content == "Hello"
    assert isinstance(obj.content, str)

    # model_validate_json(...) should also work now with the fix
    obj = Outer.model_validate_json(json_text)
    obj.content = force(obj.content)
    assert obj.content == "Hello"
    assert isinstance(obj.content, str)



def test_model_validate_json_iterable_union():
    """Test that model_validate_json correctly validates iterable in str | Iterable union"""
    model = Outer(content=[{"msg": "Hello"}, {"msg": "World"}])

    json_text = model.model_dump_json()

    # model_validate_json should correctly parse the iterable
    obj = Outer.model_validate_json(json_text)
    content_list = force(obj.content)
    assert len(content_list) == 2
    assert content_list[0]["msg"] == "Hello"
    assert content_list[1]["msg"] == "World"



