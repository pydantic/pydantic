import re

from pydantic_core import SchemaValidator, __version__


def test_main():
    v = SchemaValidator({'type': 'bool', 'model_name': 'TestModel'})
    assert repr(v) == 'SchemaValidator(validator=BoolValidator, model_name="TestModel")'

    assert v.run(True) is True


def test_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', __version__)
