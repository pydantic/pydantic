"""
This file is used to test pyright's ability to check pydantic code.

In particular pydantic provides the `@__dataclass_transform__` for `BaseModel`
and all subclasses (including `BaseSettings`), see #2721.
"""

from typing import List

from pydantic import BaseModel, BaseSettings, Field


class MyModel(BaseModel):
    x: str
    y: List[int]


m1 = MyModel(x='hello', y=[1, 2, 3])

m2 = MyModel(x='hello')  # pyright: ignore


class Knight(BaseModel):
    title: str = Field(default='Sir Lancelot')  # this is okay
    age: int = Field(23)  # this works fine at runtime but will case an error for pyright


k = Knight()  # pyright: ignore


class Settings(BaseSettings):
    x: str
    y: int


s1 = Settings.parse_obj({})

s2 = Settings()  # pyright: ignore[reportCallIssue]
