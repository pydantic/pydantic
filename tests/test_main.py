import re

from pydantic_core import SchemaValidator, __version__


def test_main():
    v = SchemaValidator({'type': 'bool'})
    assert repr(v) == 'SchemaValidator(type_validator=BoolValidator, model_name=None)'

    assert v.run(True) is True


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
