import re

import pytest

from pydantic import BaseModel, PydanticUserError, ValidationError
from pydantic.version import version_short


def test_user_error_url():
    with pytest.raises(PydanticUserError) as exc_info:
        BaseModel()

    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly\n\n'
        f'For further information visit https://errors.pydantic.dev/{version_short()}/u/base-model-instantiated'
    )


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
