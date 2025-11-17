from functools import cached_property

from pydantic import BaseModel, computed_field


class Square(BaseModel):
    side: float

    # mypy limitation, see:
    # https://mypy.readthedocs.io/en/stable/error_code_list.html#decorator-preceding-property-not-supported-prop-decorator
    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float:
        return self.side**2

    @computed_field  # type: ignore[prop-decorator]
    @cached_property
    def area_cached(self) -> float:
        return self.side**2


sq = Square(side=10)
y = 12.4 + sq.area
z = 'x' + sq.area  # type: ignore[operator]  # pyright: ignore[reportOperatorIssue]
y_cached = 12.4 + sq.area_cached
z_cached = 'x' + sq.area_cached  # type: ignore[operator]  # pyright: ignore[reportOperatorIssue]
