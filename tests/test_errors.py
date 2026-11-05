import pickle
import re
from collections.abc import Sequence
from typing import Final

import pytest
from pydantic_core import PydanticCustomError
from typing_extensions import NotRequired, Required

from pydantic import BaseModel, PydanticForbiddenQualifier, PydanticUserError, ValidationError, field_validator
from pydantic.version import version_short


def test_user_error_url():
    with pytest.raises(
        PydanticUserError,
        check=lambda e: (
            str(e)
            == (
                'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly\n\n'
                f'For further information visit https://errors.pydantic.dev/{version_short()}/u/base-model-instantiated'
            )
        ),
    ):
        BaseModel()


def test_forbidden_qualifier() -> None:
    with pytest.raises(PydanticForbiddenQualifier):

        class Model1(BaseModel):
            a: Required[int]

    with pytest.raises(PydanticForbiddenQualifier):

        class Model2(BaseModel):
            b: Final[NotRequired[str]] = 'test'


@pytest.mark.parametrize(
    'hide_input,input_str',
    ((False, 'type=greater_than, input_value=4, input_type=int'), (True, 'type=greater_than')),
)
def test_raise_validation_error_hide_input(hide_input, input_str):
    with pytest.raises(ValidationError, match=re.escape(f'Input should be greater than 5 [{input_str}]')):
        raise ValidationError.from_exception_data(
            'Foobar',
            [{'type': 'greater_than', 'loc': ('a', 2), 'input': 4, 'ctx': {'gt': 5}}],
            hide_input=hide_input,
        )


def test_pickle_validation_error_custom_error_type() -> None:
    """https://github.com/pydantic/pydantic/issues/14034"""

    class Model(BaseModel):
        seq: Sequence[str]
        a: int

        @field_validator('a')
        @classmethod
        def validate_a(cls, v: int) -> int:
            raise PydanticCustomError('custom_error', 'Custom error with {value}', {'value': v})

    with pytest.raises(ValidationError) as exc_info:
        Model(seq='not_a_sequence', a=1)

    exc = exc_info.value
    unpickled = pickle.loads(pickle.dumps(exc))

    assert unpickled.errors() == exc.errors()
    assert unpickled.errors() == [
        {
            'type': 'sequence_str',
            'loc': ('seq',),
            'msg': "'str' instances are not allowed as a Sequence value",
            'input': 'not_a_sequence',
            'ctx': {'type_name': 'str'},
        },
        {
            'type': 'custom_error',
            'loc': ('a',),
            'msg': 'Custom error with 1',
            'input': 1,
            'ctx': {'value': 1},
        },
    ]


class CustomErrorSubclass(PydanticCustomError):
    pass


class CustomErrorOverriddenNew(PydanticCustomError):
    def __new__(cls, setting: str) -> 'CustomErrorOverriddenNew':
        return super().__new__(cls, 'custom_error', 'Custom error with {setting}', {'setting': setting})


@pytest.mark.parametrize(
    'error',
    [
        PydanticCustomError('custom_error', 'Custom error with {value}', {'value': 1}),
        PydanticCustomError('custom_error', 'Custom error'),
        CustomErrorSubclass('custom_error', 'Custom error'),
        CustomErrorOverriddenNew('my_setting'),
    ],
)
def test_pickle_pydantic_custom_error(error: PydanticCustomError) -> None:
    error.extra = 'extra'
    unpickled = pickle.loads(pickle.dumps(error))

    assert type(unpickled) is type(error)
    assert unpickled.type == error.type
    assert unpickled.message_template == error.message_template
    assert unpickled.context == error.context
    assert unpickled.args == error.args
    assert unpickled.extra == 'extra'
