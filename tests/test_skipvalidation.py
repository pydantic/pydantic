import warnings
from typing import Annotated

from pydantic import BaseModel, SkipValidation
from pydantic.warnings import PydanticSkipValidationWarning


def test_skip_validation_warning():
    class MyModel(BaseModel):
        field: Annotated[int, SkipValidation]

    # Ensure no warning is raised when SkipValidation is applied
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        MyModel(field='not_an_int')  # SkipValidation should bypass validation

        # Assert no warnings of type PydanticSkipValidationWarning were raised
        assert not any(issubclass(warning.category, PydanticSkipValidationWarning) for warning in w)


def test_skip_validation_behavior():
    class MyModel(BaseModel):
        field: Annotated[int, SkipValidation]

    # Ensure the field accepts any value without validation
    instance = MyModel(field='not_an_int')
    assert instance.field == 'not_an_int'  # Validation is skipped
