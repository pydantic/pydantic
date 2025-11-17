import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs(()), ((), {})],
        [ArgsKwargs((1, 2, 3)), ((1, 2, 3), {})],
        [{'args': ()}, ((), {})],
        [{'args': (1, 2, 3)}, ((1, 2, 3), {})],
        # Also validates against other sequence types, as long as it is
        # possible to validate it as a tuple:
        [{'args': [1, 2, 3]}, ((1, 2, 3), {})],
    ),
)
def test_var_args(py_and_json: PyAndJson, input_value, expected) -> None:
    """Test valid inputs against var-args parameters:

    ```python
    def func(*args: int):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='args', schema=cs.int_schema(), mode='var_args'),
            ]
        )
    )

    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    ['input_value', 'err_loc'],
    (
        [ArgsKwargs(('not_an_int',)), (0,)],
        [
            ArgsKwargs(
                (
                    1,
                    'not_an_int',
                )
            ),
            (1,),
        ],
        [{'args': ['not_an_int']}, ('args', 0)],
        [{'args': [1, 'not_an_int']}, ('args', 1)],
    ),
)
def test_var_args_validation_error(py_and_json: PyAndJson, input_value, err_loc) -> None:
    """Test invalid inputs against var-args parameters:

    ```python
    def func(*args: int):
        ...

    func(1, 'not_an_int')
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='args', schema=cs.int_schema(), mode='var_args'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == err_loc


def test_var_args_invalid_tuple(py_and_json: PyAndJson) -> None:
    """Test invalid tuple-like input against var-args parameters in mapping validation mode."""
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='args', schema=cs.int_schema(), mode='var_args'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'args': 'not_a_tuple'})

    error = exc_info.value.errors()[0]

    assert error['type'] == 'tuple_type'
    assert error['loc'] == ('args',)
