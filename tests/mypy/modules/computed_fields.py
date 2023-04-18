from pydantic import BaseModel, computed_field


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
z = 'x' + sq.area

try:
    from functools import cached_property
except ImportError:
    pass
else:

    class Square2(BaseModel):
        side: float

        @computed_field
        @cached_property
        def area(self) -> float:
            return self.side**2

    sq = Square(side=10)
    y = 12.4 + sq.area
    z = 'x' + sq.area
