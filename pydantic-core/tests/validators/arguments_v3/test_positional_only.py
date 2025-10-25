import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    'input_value',
    [
        ArgsKwargs((1, True)),
        ArgsKwargs((1,)),
        {'a': 1, 'b': True},
        {'a': 1},
    ],
)
def test_positional_only(py_and_json: PyAndJson, input_value) -> None:
    """Test valid inputs against positional-only parameters:

    ```python
    def func(a: int, b: bool = True, /):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_only'),
                cs.arguments_v3_parameter(
                    name='b', schema=cs.with_default_schema(cs.bool_schema(), default=True), mode='positional_only'
                ),
            ]
        )
    )

    assert v.validate_test(input_value) == ((1, True), {})


def test_positional_only_validation_error(py_and_json: PyAndJson) -> None:
    """Test invalid inputs against positional-only parameters:

    ```python
    def func(a: int, /):
        ...

    func('not_an_int')
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_only'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(ArgsKwargs(('not_an_int',), {}))

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == (0,)

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'a': 'not_an_int'})

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == ('a',)


def test_positional_only_error_required(py_and_json: PyAndJson) -> None:
    """Test missing inputs against positional-only parameters:

    ```python
    def func(a: int, /):
        ...

    func()
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_only'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(ArgsKwargs((), {}))

    error = exc_info.value.errors()[0]

    assert error['type'] == 'missing_positional_only_argument'
    assert error['loc'] == (0,)

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({})

    error = exc_info.value.errors()[0]

    assert error['type'] == 'missing_positional_only_argument'
    assert error['loc'] == ('a',)
