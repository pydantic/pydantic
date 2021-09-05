import random
from functools import cached_property

from pydantic import BaseModel, computed_field


class Square(BaseModel):
    width: float

    @computed_field(title='The area', description='the area of the square')
    @property  # can be omitted as explained above
    def area(self) -> float:
        return round(self.width ** 2, 2)

    @area.setter
    def area(self, new_area: float) -> None:
        self.width = new_area ** .5

    @computed_field(alias='the magic number', repr=False)
    @cached_property
    def random_number(self) -> int:
        """An awesome number"""
        return random.randint(0, 1_000)

    @computed_field(exclude=True)  # exclude it in serialization
    def is_dot(self) -> bool:
        return self.width == 0


square = Square(width=1.3)

# `random_number` does not appear in representation
print(repr(square))

print(square.random_number)

# same random number as before (cached as expected) and `is_dot` is excluded
print(square.dict())

square.area = 4

print(square.json(by_alias=True))

# Computed fields that don't have a setter have `readOnly` attribute
print(Square.schema_json(indent=2))
