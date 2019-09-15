from typing import Type

from pydantic import BaseModel
from pydantic import ValidationError

class Foo:
    pass

class LenientSimpleModel(BaseModel):
    any_class_goes: Type

LenientSimpleModel(any_class_goes=int)
LenientSimpleModel(any_class_goes=Foo)
try:
    LenientSimpleModel(just_subclasses=Foo())
except ValidationError as e:
    print(e)
"""
1 validation error
any_class_goes
  subclass of type expected (type=type_error.class)
"""
