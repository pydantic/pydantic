import pytest

from pydantic import BaseModel as V1BaseModel

try:
    from pydantic_next import BaseModel as V2BaseModel
except ModuleNotFoundError:
    pytestmark = pytest.mark.skip(reason='pydantic_next not installed')


def test_both_packages():
    class NextModel(V2BaseModel):
        a: str

    class Model(V1BaseModel):
        a: str
