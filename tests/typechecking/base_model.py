"""
This file is used to test pyright's ability to check Pydantic's `BaseModel` related code.
"""

from typing_extensions import assert_type

from pydantic import BaseModel, Field
from pydantic.fields import ComputedFieldInfo, FieldInfo


class MyModel(BaseModel):
    x: str
    y: list[int]
    z: int = 1


m1 = MyModel(x='hello', y=[1, 2, 3])

m2 = MyModel(x='hello')  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]

m3 = MyModel(x='hello', y=[1, '2', b'3'])  # type: ignore[list-item]  # pyright: ignore[reportArgumentType]

m1.z + 'not an int'  # type: ignore[operator]  # pyright: ignore[reportOperatorIssue]

m1.foobar  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]


class Knight(BaseModel):
    title: str = Field(default='Sir Lancelot')  # this is okay
    age: int = Field(23)  # this works fine at runtime but will case an error for pyright


k = Knight()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]

assert_type(Knight.model_fields, dict[str, FieldInfo])
assert_type(Knight.model_computed_fields, dict[str, ComputedFieldInfo])
# Mypy does not report the deprecated access (https://github.com/python/mypy/issues/18323):
assert_type(k.model_fields, dict[str, FieldInfo])  # pyright: ignore[reportDeprecated]
assert_type(k.model_computed_fields, dict[str, ComputedFieldInfo])  # pyright: ignore[reportDeprecated]
