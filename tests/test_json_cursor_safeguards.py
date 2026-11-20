"""Checked cursor skips retain JSON validity across input kinds and deferred fields."""

import json
from typing import Any

import pytest
from pydantic_core import from_json

from pydantic import BaseModel, TypeAdapter, ValidationError


@pytest.mark.parametrize('input_kind', ['str', 'bytes', 'bytearray'])
@pytest.mark.parametrize(
    'document',
    [
        '{"a":1,"ignored":{"text":"日本語 café","brackets":"[{}]"},"b":"valid"}',
        '{"b":"café","a":1}',
        '{"b":"café","b":"valid","a":1}',
    ],
)
def test_checked_skips_accept_valid_unicode(input_kind: str, document: str) -> None:
    """https://github.com/pydantic/pydantic/pull/14347"""

    class Model(BaseModel):
        a: int
        b: str

    data = document if input_kind == 'str' else document.encode()
    if input_kind == 'bytearray':
        data = bytearray(data)
    expected = 'café' if document == '{"b":"café","a":1}' else 'valid'
    assert Model.model_validate_json(data).model_dump() == {'a': 1, 'b': expected}


@pytest.mark.parametrize('as_bytearray', [False, True])
@pytest.mark.parametrize(
    'document',
    [
        b'{"a":1,"first":"valid","second":"\xff","b":"valid"}',
        b'{"b":"\xff","b":"valid","a":1}',
        b'{"a":1,"ignored":{"nested":"\xff"},"b":"valid"}',
    ],
)
def test_checked_skips_reject_malformed_bytes_anywhere(as_bytearray: bool, document: bytes) -> None:
    """https://github.com/pydantic/pydantic/pull/14347"""

    class Model(BaseModel):
        a: int
        b: str

    data = bytearray(document) if as_bytearray else document
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        Model.model_validate_json(data)


@pytest.mark.parametrize('input_kind', ['str', 'bytes', 'bytearray'])
@pytest.mark.parametrize(
    'escape', [r'\ud800', r'\udfff', r'\ud800\u0041', r'\ud800\ud800', r'\udc00\ud800', r'\uZZZZ', r'\x41']
)
def test_checked_skips_still_validate_json_escapes(input_kind: str, escape: str) -> None:
    """https://github.com/pydantic/pydantic/pull/14347"""

    class Model(BaseModel):
        a: int

    document = '{"a":1,"ignored":"' + escape + '"}'
    data = document if input_kind == 'str' else document.encode()
    if input_kind == 'bytearray':
        data = bytearray(data)
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        Model.model_validate_json(data)


@pytest.mark.parametrize('surrogate', ['\ud800', '\udfff'])
def test_checked_skips_reject_python_string_surrogates(surrogate: str) -> None:
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'string_unicode'):
        Model.model_validate_json('{"a":1,"ignored":"' + surrogate + '"}')


@pytest.mark.parametrize('route', ['ignored', 'materialized', 'deferred', 'overwritten', 'list_item', 'nested_model'])
@pytest.mark.parametrize('depth', [198, 199, 200, 201])
@pytest.mark.parametrize('leaf', ['1', '[]', '{}'])
def test_cursor_subtrees_retain_document_depth(route: str, depth: int, leaf: str) -> None:
    class Model(BaseModel):
        a: int
        b: Any = None

    subtree = '[' * depth + leaf + ']' * depth
    if route == 'ignored':
        document = '{"a":1,"ignored":' + subtree + '}'
        adapter = TypeAdapter(Model)
    elif route == 'materialized':
        document = '{"a":1,"b":' + subtree + '}'
        adapter = TypeAdapter(Model)
    elif route == 'deferred':
        document = '{"b":' + subtree + ',"a":1}'
        adapter = TypeAdapter(Model)
    elif route == 'overwritten':
        document = '{"b":' + subtree + ',"b":0,"a":1}'
        adapter = TypeAdapter(Model)
    elif route == 'list_item':
        document = '[' + subtree + ']'
        adapter = TypeAdapter(list[Any])
    else:
        document = '[{"a":1,"b":' + subtree + '}]'
        adapter = TypeAdapter(list[Model])
    try:
        from_json(document)
    except ValueError:
        with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
            adapter.validate_json(document)
    else:
        adapter.validate_json(document)


def test_cursor_depth_ignores_escaped_string_brackets() -> None:
    class Model(BaseModel):
        a: int
        b: Any

    text = '[{\\"' * 500
    document = json.dumps({'b': [text], 'ignored': [text], 'a': 1})
    assert Model.model_validate_json(document).b == [text]
