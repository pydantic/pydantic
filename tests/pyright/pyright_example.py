"""
This file is used to test pyright's ability to check pydantic code.
"""

from functools import cached_property
from typing import Annotated, List

from pydantic import BaseModel, Field, computed_field
from pydantic.type_adapter import TypeAdapter


class MyModel(BaseModel):
    x: str
    y: List[int]


m1 = MyModel(x='hello', y=[1, 2, 3])

m2 = MyModel(x='hello')  # pyright: ignore


class Knight(BaseModel):
    title: str = Field(default='Sir Lancelot')  # this is okay
    age: int = Field(23)  # this works fine at runtime but will case an error for pyright


k = Knight()  # pyright: ignore


class Square(BaseModel):
    side: float

    @computed_field
    @property
    def area(self) -> float:
        return self.side**2

    @area.setter
    def area(self, area: float) -> None:
        self.side = area**0.5


sq = Square(side=10)
y = 12.4 + sq.area
z = 'x' + sq.area  # type: ignore


class Square2(BaseModel):
    side: float

    @computed_field
    @cached_property
    def area(self) -> float:
        return self.side**2


sq = Square(side=10)
y = 12.4 + sq.area
z = 'x' + sq.area  # type: ignore


# TypeAdapter will correctly infer the type of int
ta1 = TypeAdapter(int)
assert ta1.validate_json('123') + 1 == 124
# But currently cannot infer more complex "special forms" and defaults to TypeAdapter[Any]
ta2 = TypeAdapter(Annotated[int, Field(gt=0)])
assert ta2.validate_python(999) + 1 == 1000
# If you want these to be typed, you can use a type hint as follows:
ta3: TypeAdapter[int] = TypeAdapter(Annotated[int, Field(gt=0)])
assert ta3.validate_python(999) + 1 == 1000
