import re

from pydantic_core import __version__, parse


def test_main():
    v = parse({'type': 'string'}, None)
    assert v == 'String { enum_: None, const_: None, pattern: None, max_length: None, min_length: None }'


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
