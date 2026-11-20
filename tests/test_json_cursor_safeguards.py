"""Checked cursor skips retain JSON validity across input kinds and deferred fields."""

import pytest

from pydantic import BaseModel, ValidationError


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
