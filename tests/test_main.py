import re

from pydantic_core import SchemaValidator, __version__


def test_main():
    v = SchemaValidator({'type': 'string'})
    assert repr(v).startswith('SchemaValidator(String(')

    assert v.validate('foo') == 'foo'


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
