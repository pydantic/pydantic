from typing import Any, Dict, List, Optional
from unittest import TestCase
from unittest.mock import ANY

import pytest
from typing_extensions import LiteralString, Self, override

from pydantic_core import ErrorDetails, InitErrorDetails, PydanticCustomError, ValidationError


def test_validation_error_subclassable():
    """Assert subclassable and inheritance hierarchy as expected"""

    class CustomValidationError(ValidationError):
        pass

    with pytest.raises(ValidationError) as exception_info:
        raise CustomValidationError.from_exception_data(
            'My CustomError',
            [
                InitErrorDetails(
                    type='value_error',
                    loc=('myField',),
                    msg='This is my custom error.',
                    input='something invalid',
                    ctx={
                        'myField': 'something invalid',
                        'error': "'something invalid' is not a valid value for 'myField'",
                    },
                )
            ],
        )
    assert isinstance(exception_info.value, CustomValidationError)


def test_validation_error_loc_overrides():
    """Override methods in rust pyclass and assert change in behavior: ValidationError.errors"""

    class CustomLocOverridesError(ValidationError):
        """Unnests some errors"""

        @override
        def errors(
            self, *, include_url: bool = True, include_context: bool = True, include_input: bool = True
        ) -> List[ErrorDetails]:
            errors = super().errors(
                include_url=include_url, include_context=include_context, include_input=include_input
            )
            return [{**error, 'loc': error['loc'][1:]} for error in errors]

    with pytest.raises(CustomLocOverridesError) as exception_info:
        raise CustomLocOverridesError.from_exception_data(
            'My CustomError',
            [
                InitErrorDetails(
                    type='value_error',
                    loc=(
                        'hide_this',
                        'myField',
                    ),
                    msg='This is my custom error.',
                    input='something invalid',
                    ctx={
                        'myField': 'something invalid',
                        'error': "'something invalid' is not a valid value for 'myField'",
                    },
                ),
                InitErrorDetails(
                    type='value_error',
                    loc=(
                        'hide_this',
                        'myFieldToo',
                    ),
                    msg='This is my custom error.',
                    input='something invalid',
                    ctx={
                        'myFieldToo': 'something invalid',
                        'error': "'something invalid' is not a valid value for 'myFieldToo'",
                    },
                ),
            ],
        )

    TestCase().assertCountEqual(
        exception_info.value.errors(),
        [
            {
                'type': 'value_error',
                'loc': ('myField',),
                'msg': "Value error, 'something invalid' is not a valid value for 'myField'",
                'input': 'something invalid',
                'ctx': {
                    'error': "'something invalid' is not a valid value for 'myField'",
                    'myField': 'something invalid',
                },
                'url': ANY,
            },
            {
                'type': 'value_error',
                'loc': ('myFieldToo',),
                'msg': "Value error, 'something invalid' is not a valid value for 'myFieldToo'",
                'input': 'something invalid',
                'ctx': {
                    'error': "'something invalid' is not a valid value for 'myFieldToo'",
                    'myFieldToo': 'something invalid',
                },
                'url': ANY,
            },
        ],
    )


def test_custom_pydantic_error_subclassable():
    """Assert subclassable and inheritance hierarchy as expected"""

    class MyCustomError(PydanticCustomError):
        pass

    with pytest.raises(PydanticCustomError) as exception_info:
        raise MyCustomError(
            'not_my_custom_thing',
            "value is not compatible with my custom field, got '{wrong_value}'",
            {'wrong_value': 'non compatible value'},
        )
    assert isinstance(exception_info.value, MyCustomError)


def test_custom_pydantic_error_overrides():
    """Override methods in rust pyclass and assert change in behavior: PydanticCustomError.__new__"""

    class CustomErrorWithCustomTemplate(PydanticCustomError):
        @override
        def __new__(
            cls, error_type: LiteralString, my_custom_setting: str, context: Optional[Dict[str, Any]] = None
        ) -> Self:
            message_template = (
                "'{my_custom_value}' setting requires a specific my custom field value, got '{wrong_value}'"
            )
            context = {**context, 'my_custom_value': my_custom_setting}
            return super().__new__(cls, error_type, message_template, context)

    with pytest.raises(CustomErrorWithCustomTemplate) as exception_info:
        raise CustomErrorWithCustomTemplate(
            'not_my_custom_thing', 'my_setting', {'wrong_value': 'non compatible value'}
        )

    assert (
        exception_info.value.message()
        == "'my_setting' setting requires a specific my custom field value, got 'non compatible value'"
    )
