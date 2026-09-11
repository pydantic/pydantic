"""Asserts that no explicit Any error is raised when using dynamic aliases (which results in constructors being synthesized as `(**kwargs: Any) -> None`)."""

from pydantic import AliasChoices, BaseModel, Field


class ModelWithAliasChoices(BaseModel):
    test_field: str = Field(default='', validation_alias=AliasChoices('choice', 'other_choice'))
