import pytest

from pydantic import BaseModel, PydanticUserError


def test_user_error_url():
    with pytest.raises(PydanticUserError) as exc_info:
        BaseModel()

    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly\n\n'
        'For further information visit <TODO: Set up the errors URLs>/base-model-instantiated'
    )
