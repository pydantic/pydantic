import re
from typing import Any

import pytest

from pydantic import BaseModel, PydanticUserError, ValidationError
from pydantic.version import VERSION


def test_user_error_url():
    with pytest.raises(PydanticUserError) as exc_info:
        BaseModel()

    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly\n\n'
        f'For further information visit https://errors.pydantic.dev/{VERSION}/u/base-model-instantiated'
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


def test_original_exceptions_are_accessible():
    from pydantic import BaseModel, field_validator

    class Model(BaseModel):
        foo: int
        bar: int

        @field_validator('foo')
        def val_foo(cls, value: Any) -> int:
            try:
                assert value > 5, 'Must be greater than 5'
            except AssertionError as e:
                raise ValueError('some value error') from e
            return value

        @field_validator('bar')
        def val_bar(cls, value: Any) -> int:
            try:
                assert value > 5, 'Must be greater than 5'
            except AssertionError as e:
                e.add_note('added some note')
                raise e
            return value

    with pytest.raises(ValidationError) as e:
        Model(foo=4, bar=4)

    foo_error = e.value.errors()[0]['ctx']['error']
    assert isinstance(foo_error, ValueError)
    assert str(foo_error) == 'some value error'
    assert isinstance(foo_error.__cause__, AssertionError)
    assert str(foo_error.__cause__) == 'Must be greater than 5'

    bar_error = e.value.errors()[1]['ctx']['error']
    assert isinstance(bar_error, AssertionError)
    assert str(bar_error) == 'Must be greater than 5'
    assert str(bar_error.__notes__) == ['added some note']
