import pytest
from typing_extensions import sentinel

from pydantic import BaseModel, TypeAdapter, ValidationError

MINE = sentinel('MINE')
OTHER = sentinel('OTHER')


def test_pep661_sentinel_in_union_and_standalone_field() -> None:
    class ModelA(BaseModel):
        x: int | MINE = MINE  # type: ignore[valid-type]

    class ModelB(BaseModel):
        x: MINE = MINE  # type: ignore[valid-type]

    assert ModelA.model_validate({'x': MINE}).x is MINE
    assert ModelA.model_validate({'x': 1}).x == 1
    assert ModelA.model_validate({}).x is MINE
    assert ModelA().model_dump() == {'x': MINE}

    with pytest.raises(ValidationError):
        ModelA.model_validate({'x': 'MINE'})

    with pytest.raises(ValidationError):
        ModelA.model_validate({'x': OTHER})

    assert ModelB().x is MINE
    assert ModelB.model_validate({'x': MINE}).x is MINE
    assert ModelB().model_dump() == {'x': MINE}

    with pytest.raises(ValidationError):
        ModelB.model_validate({'x': 'MINE'})


def test_pep661_sentinel_type_adapter() -> None:
    ta = TypeAdapter(int | MINE)  # type: ignore[valid-type]
    assert ta.validate_python(MINE) is MINE
    assert ta.validate_python(42) == 42

    with pytest.raises(ValidationError):
        ta.validate_python(OTHER)
