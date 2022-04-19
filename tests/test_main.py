import pytest

from pydantic_core import SchemaValidator, ValidationError


@pytest.mark.parametrize(
    'input_value,output_value',
    [
        (False, False),
        (True, True),
        (0, False),
        (1, True),
        ('yes', True),
        ('no', False),
        ('true', True),
        ('false', False),
    ],
)
def test_bool(input_value, output_value):
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert v.validate_python(input_value) == output_value


def test_bool_error():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=BoolValidator)'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')

    assert str(exc_info.value) == (
        '1 validation error for TestModel\n'
        '  Value must be a valid boolean, unable to interpret input (kind=bool_parsing)'
    )


def test_repr():
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert repr(v) == 'SchemaValidator(title="TestModel", validator=BoolValidator)'


def test_str():
    v = SchemaValidator({'type': 'str', 'title': 'TestModel'})
    assert v.validate_python('test') == 'test'


def test_str_constrained():
    v = SchemaValidator({'type': 'str-constrained', 'max_length': 5, 'title': 'TestModel'})
    assert v.validate_python('test') == 'test'

    with pytest.raises(ValidationError, match='String must have at most 5 characters'):
        v.validate_python('test long')
