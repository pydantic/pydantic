"""
This file is used to test pyright's ability to check Pydantic's `BaseModel` related code.
"""

from functools import cached_property

from typing_extensions import assert_type

from pydantic import BaseModel, Field, computed_field


class MyModel(BaseModel):
    x: str
    y: list[int]


m1 = MyModel(x='hello', y=[1, 2, 3])

m2 = MyModel(x='hello')  # pyright: ignore[reportCallIssue]


class Knight(BaseModel):
    title: str = Field(default='Sir Lancelot')  # this is okay
    age: int = Field(23)  # this works fine at runtime but will case an error for pyright


k = Knight()  # pyright: ignore[reportCallIssue]


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
assert_type(sq.area, float)


class Square2(BaseModel):
    side: float

    @computed_field
    @cached_property
    def area(self) -> float:
        return self.side**2


sq = Square(side=10)
assert_type(sq.area, float)
