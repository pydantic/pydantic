import re

from pydantic_core import SchemaValidator, __version__


def test_main():
    v = SchemaValidator({'type': 'str'})
    debug(repr(v))
    assert repr(v) == 'SchemaValidator(type_validator=SimpleStrValidator, external_validator=None)'

    assert v.validate('foo') == 'foo'


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
