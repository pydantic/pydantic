import pytest

from pydantic_core import SchemaValidator, ValidationError


def func():
    return 42


class Foo:
    pass


class CallableClass:
    def __call__(self, *args, **kwargs):
        pass


def test_callable():
    v = SchemaValidator({'type': 'callable'})
    assert v.validate_python(func) == func
    assert v.isinstance_python(func) is True
    assert v.isinstance_json('"func"') is False

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert exc_info.value.errors() == [
        {'type': 'callable_type', 'loc': (), 'msg': 'Input should be callable', 'input': 42}
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (func, True),
        (lambda: 42, True),
        (lambda x: 2 * 42, True),
        (dict, True),
        (Foo, True),
        (Foo(), False),
        (4, False),
        ('ddd', False),
        ([], False),
        ((1,), False),
        (CallableClass, True),
        (CallableClass(), True),
    ],
)
def test_callable_cases(input_value, expected):
    v = SchemaValidator({'type': 'callable'})
    assert v.isinstance_python(input_value) == expected


def test_repr():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'int'}, {'type': 'callable'}]})
    assert v.isinstance_python(4) is True
    assert v.isinstance_python(func) is True
    assert v.isinstance_python('foo') is False

    with pytest.raises(ValidationError, match=r'callable\s+Input should be callable'):
        v.validate_python('foo')
