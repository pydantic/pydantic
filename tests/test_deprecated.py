import pytest

from pydantic import (
    BaseModel,
    PydanticDeprecatedSince211,
    computed_field,
)

# `pytest.warns/raises()` is thread unsafe. As these tests are meant to be
# removed in V3, we just mark all tests as thread unsafe
pytestmark = pytest.mark.thread_unsafe


def test_fields():
    class Model(BaseModel):
        x: int
        y: int = 2

        @computed_field
        @property
        def area(self) -> int:
            return self.x * self.y

    m = Model(x=1)
    assert len(Model.model_fields) == 2

    with pytest.warns(PydanticDeprecatedSince211, match="Accessing the 'model_fields' attribute"):
        assert len(m.model_fields) == 2

    with pytest.warns(PydanticDeprecatedSince211, match="Accessing the 'model_computed_fields' attribute"):
        assert len(m.model_computed_fields) == 1
