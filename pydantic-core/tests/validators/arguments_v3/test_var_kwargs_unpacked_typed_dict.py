import pytest

from pydantic_core import ArgsKwargs, ValidationError
from pydantic_core import core_schema as cs

from ...conftest import Err, PyAndJson


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    (
        [ArgsKwargs((), {'x': 1}), ((), {'x': 1})],
        [ArgsKwargs((), {'x': 1, 'z': True}), ((), {'x': 1, 'y': True})],
        [ArgsKwargs((), {}), Err('', [{'type': 'missing', 'loc': ('x',)}])],
        [ArgsKwargs((), {'x': 'not_an_int'}), Err('', [{'type': 'int_parsing', 'loc': ('x',)}])],
        [ArgsKwargs((), {'x': 1, 'y': True}), Err('', [{'type': 'extra_forbidden', 'loc': ('y',)}])],
        [{'kwargs': {'x': 1}}, ((), {'x': 1})],
        [{'kwargs': {'x': 1, 'z': True}}, ((), {'x': 1, 'y': True})],
        [{'kwargs': {}}, Err('', [{'type': 'missing', 'loc': ('kwargs', 'x')}])],
        [{}, Err('', [{'type': 'missing', 'loc': ('kwargs', 'x')}])],
        [
            {'kwargs': {'x': 'not_an_int'}},
            Err(
                '',
                [
                    {
                        'type': 'int_parsing',
                        'loc': (
                            'kwargs',
                            'x',
                        ),
                    }
                ],
            ),
        ],
        [
            {'kwargs': {'x': 1, 'y': True}},
            Err(
                '',
                [
                    {
                        'type': 'extra_forbidden',
                        'loc': (
                            'kwargs',
                            'y',
                        ),
                    }
                ],
            ),
        ],
    ),
)
def test_var_kwargs(py_and_json: PyAndJson, input_value, expected) -> None:
    """Test (in)valid inputs against var-args parameters (unpacked typed dict):

    ```python
    class TD(TypedDict, total=false):
        x: Required[int]
        y: Annotated[bool, Field(validation_alias='z')]

    def func(**kwargs: Unpack[TD]):
        ...
    ```
    """
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(
                    name='kwargs',
                    schema=cs.typed_dict_schema(
                        {
                            'x': cs.typed_dict_field(
                                schema=cs.int_schema(),
                                required=True,
                            ),
                            'y': cs.typed_dict_field(
                                schema=cs.bool_schema(),
                                required=False,
                                validation_alias='z',
                            ),
                        },
                        extra_behavior='forbid',
                    ),
                    mode='var_kwargs_unpacked_typed_dict',
                ),
            ]
        )
    )

    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test(input_value)

        error = exc_info.value.errors()[0]

        assert error['type'] == expected.errors[0]['type']
        assert error['loc'] == expected.errors[0]['loc']
    else:
        assert v.validate_test(input_value) == expected


def test_var_kwargs_invalid_dict(py_and_json: PyAndJson) -> None:
    """Test invalid dict-like input against var-kwargs parameters in mapping validation mode."""
    v = py_and_json(
        cs.arguments_v3_schema(
            [
                cs.arguments_v3_parameter(
                    name='kwargs', schema=cs.typed_dict_schema({}), mode='var_kwargs_unpacked_typed_dict'
                ),
            ]
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'kwargs': 'not_a_dict'})

    error = exc_info.value.errors()[0]

    assert error['type'] == 'dict_type'
    assert error['loc'] == ('kwargs',)
