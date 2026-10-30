from typing import Any

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    PydanticDeprecatedSince211,
    PydanticUserError,
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


def test_modify_schema_error():
    with pytest.raises(
        PydanticUserError,
        match='The `__modify_schema__` method is not supported in Pydantic v2. '
        'Use `__get_pydantic_json_schema__` instead in class `Model`.',
    ):

        class Model(BaseModel):
            @classmethod
            def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
                pass


def test_modify_schema_on_nested_class_error() -> None:
    class SomeLongName:
        @classmethod
        def __modify_schema__(cls, field_schema):
            pass

    with pytest.raises(
        PydanticUserError,
        match='The `__modify_schema__` method is not supported in Pydantic v2. '
        'Use `__get_pydantic_json_schema__` instead in class `SomeLongName`.',
    ):

        class B(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)

            a: SomeLongName
