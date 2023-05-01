import pytest

from pydantic import BaseModel, PydanticUserError
from pydantic.version import VERSION


def test_user_error_url():
    with pytest.raises(PydanticUserError) as exc_info:
        BaseModel()

    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        'Pydantic models should inherit from BaseModel, BaseModel cannot be instantiated directly\n\n'
        f'For further information visit https://errors.pydantic.dev/{VERSION}/u/base-model-instantiated'
    )
