import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    'input_value',
    [
        ArgsKwargs((), {'a': 1, 'b': True}),
        ArgsKwargs((), {'a': 1}),
        {'a': 1, 'b': True},
        {'a': 1},
    ],
)
def test_keyword_only(py_and_json: PyAndJson, input_value) -> None:
    """Test valid inputs against keyword-only parameters:

    ```python
    def func(*, a: int, b: bool = True):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='keyword_only'),
                cs.arguments_v3_parameter(
                    name='b', schema=cs.with_default_schema(cs.bool_schema(), default=True), mode='keyword_only'
                ),
            ]
        )
    )

    assert v.validate_test(input_value) == ((), {'a': 1, 'b': True})


@pytest.mark.parametrize(
    'input_value',
    [ArgsKwargs((), {'a': 'not_an_int'}), {'a': 'not_an_int'}],
)
def test_keyword_only_validation_error(py_and_json: PyAndJson, input_value) -> None:
    """Test invalid inputs against keyword-only parameters:

    ```python
    def func(*, a: int):
        ...

    func('not_an_int')
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='keyword_only'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == ('a',)


@pytest.mark.parametrize(
    'input_value',
    [ArgsKwargs((), {}), {}],
)
def test_keyword_only_error_required(py_and_json: PyAndJson, input_value) -> None:
    """Test missing inputs against keyword-only parameters:

    ```python
    def func(*, a: int):
        ...

    func()
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='keyword_only'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'missing_keyword_only_argument'
    assert error['loc'] == ('a',)
