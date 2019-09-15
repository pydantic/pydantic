from typing import Type

from pydantic import BaseModel
from pydantic import ValidationError

class Foo:
    pass

class Bar(Foo):
    pass

class Other:
    pass

class SimpleModel(BaseModel):
    just_subclasses: Type[Foo]


SimpleModel(just_subclasses=Foo)
SimpleModel(just_subclasses=Bar)
try:
    SimpleModel(just_subclasses=Other)
except ValidationError as e:
    print(e)
"""
1 validation error
just_subclasses
  subclass of Foo expected (type=type_error.class)
"""
