import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs(()), ((), {})],
        [ArgsKwargs((), {'a': 1, 'b': 2}), ((), {'a': 1, 'b': 2})],
        [{}, ((), {})],
        [{'kwargs': {'a': 1, 'b': 2}}, ((), {'a': 1, 'b': 2})],
    ),
)
def test_var_kwargs(py_and_json: PyAndJson, input_value, expected) -> None:
    """Test valid inputs against var-args parameters (uniform):

    ```python
    def func(**kwargs: int):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='kwargs', schema=cs.int_schema(), mode='var_kwargs_uniform'),
            ]
        )
    )

    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    ['input_value', 'err_loc'],
    (
        [ArgsKwargs((), {'a': 'not_an_int'}), ('a',)],
        [ArgsKwargs((), {'a': 1, 'b': 'not_an_int'}), ('b',)],
        [{'kwargs': {'a': 'not_an_int'}}, ('kwargs', 'a')],
        [{'kwargs': {'a': 1, 'b': 'not_an_int'}}, ('kwargs', 'b')],
    ),
)
def test_var_kwargs_validation_error(py_and_json: PyAndJson, input_value, err_loc) -> None:
    """Test invalid inputs against var-args parameters (uniform):

    ```python
    def func(**kwargs: int):
        ...

    func(a='not_an_int')
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='kwargs', schema=cs.int_schema(), mode='var_kwargs_uniform'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == err_loc


def test_var_kwargs_invalid_dict(py_and_json: PyAndJson) -> None:
    """Test invalid dict-like input against var-kwargs parameters in mapping validation mode."""
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='kwargs', schema=cs.int_schema(), mode='var_kwargs_uniform'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'kwargs': 'not_a_dict'})

    error = exc_info.value.errors()[0]

    assert error['type'] == 'dict_type'
    assert error['loc'] == ('kwargs',)
