# from __future__ import annotations
from typing import ForwardRef, Optional

import pytest

from pydantic.main import BaseModel


def test_missing_annotation_warning_defaults_to_true():
    
    with pytest.raises(UserWarning, match='is not fully defined'):
        
        Bar = ForwardRef('Bar')
        
        class Foo(BaseModel):
            a: Bar
        
        class Bar(BaseModel):
            foo: Optional[Foo] = None


def test_missing_annotation_warning_disabled_in_config():

    Bar = ForwardRef('Bar')
    
    class Foo(BaseModel):
        b: Bar
        
        class Config:
            warn_on_undefined_types = False

    assert Foo.__pydantic_model_complete__ == False

    class Bar(BaseModel):
        foo: Optional[Foo] = None
    
    assert Bar.__pydantic_model_complete__ == True
    
    Foo.model_rebuild()
    assert Foo.__pydantic_model_complete__ == True
    assert Bar.__pydantic_model_complete__ == True


def test_user_warning():
    
    Bar = ForwardRef('Bar')

    class Foo(BaseModel):
        b: Bar
        
        class Config:
            warn_on_undefined_types = False
        
    class Bar(BaseModel):
        foo: Optional[Foo] = None

