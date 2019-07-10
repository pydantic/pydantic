from typing import Optional, Union

from typing_extensions import Literal

from pydantic import BaseModel


class Dessert(BaseModel):
    kind: str


class Pie(Dessert):
    kind: Literal['pie']
    flavor: Optional[str]


class ApplePie(Pie):
    flavor: Literal['apple']


class PumpkinPie(Pie):
    flavor: Literal['pumpkin']


class Meal(BaseModel):
    dessert: Union[ApplePie, PumpkinPie, Pie, Dessert]


assert type(Meal(dessert={'kind': 'pie', 'flavor': 'apple'}).dessert) is ApplePie
assert type(Meal(dessert={'kind': 'pie', 'flavor': 'pumpkin'}).dessert) is PumpkinPie
assert type(Meal(dessert={'kind': 'pie'}).dessert) is Pie
assert type(Meal(dessert={'kind': 'cake'}).dessert) is Dessert
