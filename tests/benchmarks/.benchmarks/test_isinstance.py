import pytest

from pydantic import BaseModel


class ModelV2(BaseModel):
    my_str: str


mv2 = ModelV2(my_str='hello')


@pytest.mark.benchmark
def isinstance_basemodel() -> None:
    assert isinstance(mv2, BaseModel)
