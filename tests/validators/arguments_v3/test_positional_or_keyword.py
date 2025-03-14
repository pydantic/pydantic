import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs((1, True)), ((1, True), {})],
        [ArgsKwargs((1,)), ((1,), {'b': True})],
        [ArgsKwargs((1,), {'b': True}), ((1,), {'b': True})],
        [ArgsKwargs((), {'a': 1, 'b': True}), ((), {'a': 1, 'b': True})],
        [{'a': 1, 'b': True}, ((1, True), {})],
        [{'a': 1}, ((1, True), {})],
    ),
)
def test_positional_or_keyword(py_and_json: PyAndJson, input_value, expected) -> None:
    """Test valid inputs against positional-or-keyword parameters:

    ```python
    def func(a: int, b: bool = True):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_or_keyword'),
                cs.arguments_v3_parameter(
                    name='b',
                    schema=cs.with_default_schema(cs.bool_schema(), default=True),
                    mode='positional_or_keyword',
                ),
            ]
        )
    )

    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    ['input_value', 'err_loc'],
    (
        [ArgsKwargs(('not_an_int',), {}), (0,)],
        [ArgsKwargs((), {'a': 'not_an_int'}), ('a',)],
        [{'a': 'not_an_int'}, ('a',)],
    ),
)
def test_positional_or_keyword_validation_error(py_and_json: PyAndJson, input_value, err_loc) -> None:
    """Test invalid inputs against positional-or-keyword parameters:

    ```python
    def func(a: int):
        ...

    func('not_an_int')
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_or_keyword'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'int_parsing'
    assert error['loc'] == err_loc


@pytest.mark.parametrize(
    'input_value',
    [ArgsKwargs((), {}), {}],
)
def test_positional_only_error_required(py_and_json: PyAndJson, input_value) -> None:
    """Test missing inputs against positional-or-keyword parameters:

    ```python
    def func(a: int):
        ...

    func()
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(name='a', schema=cs.int_schema(), mode='positional_or_keyword'),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(input_value)

    error = exc_info.value.errors()[0]

    assert error['type'] == 'missing_argument'
    assert error['loc'] == ('a',)
