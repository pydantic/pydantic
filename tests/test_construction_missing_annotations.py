from __future__ import annotations

from typing import ForwardRef

import pytest

from pydantic.main import BaseModel


def test_missing_annotation_warning_defaults_to_true():

    with pytest.raises(UserWarning, match='is not fully defined'):

        Bar = ForwardRef('Bar')

        class Foo(BaseModel):
            a: Bar

        class Bar(BaseModel):
            foo: Foo | None = None


def test_missing_annotation_warning_disabled_in_config():

    Bar = ForwardRef('Bar')

    class Foo(BaseModel):
        b: Bar

        class Config:
            warn_on_undefined_types = False

    assert Foo.__pydantic_model_complete__ is False

    class Bar(BaseModel):
        foo: Foo | None = None

    assert Bar.__pydantic_model_complete__ is True

    Foo.model_rebuild()
    assert Foo.__pydantic_model_complete__ is True
    assert Bar.__pydantic_model_complete__ is True


def test_user_warning():

    Bar = ForwardRef('Bar')

    class Foo(BaseModel):
        b: Bar

        class Config:
            warn_on_undefined_types = False

    class Bar(BaseModel):
        foo: Foo | None = None
