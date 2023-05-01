import pytest

import pydantic

try:
    import pydantic_next
except ModuleNotFoundError:
    pytestmark = pytest.mark.skip(reason='pydantic_next not installed')


def test_both_packages():
    class NextModel(pydantic_next.BaseModel):
        a: str

    class Model(pydantic.BaseModel):
        a: str
