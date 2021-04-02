from pydantic import BaseModel, ComputedField


class Rectangle(BaseModel):
    width: int
    length: int
    area: int = ComputedField(lambda self: self.width * self.length)


print(Rectangle(width=3, length=2).dict())
