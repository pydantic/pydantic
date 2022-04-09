import re

from pydantic_core import SchemaValidator, __version__


def test_main():
    v = SchemaValidator({'type': 'bool'})
    assert repr(v) == 'SchemaValidator(type_validator=BoolValidator, external_validator=None)'

    assert v(True) is True


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
