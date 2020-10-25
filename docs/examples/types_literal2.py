from typing import ClassVar, List, Union

from typing import Literal

from pydantic import BaseModel, ValidationError


class Cake(BaseModel):
    kind: Literal['cake']
    required_utensils: ClassVar[List[str]] = ['fork', 'knife']


class IceCream(BaseModel):
    kind: Literal['icecream']
    required_utensils: ClassVar[List[str]] = ['spoon']


class Meal(BaseModel):
    dessert: Union[Cake, IceCream]


print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
try:
    Meal(dessert={'kind': 'pie'})
except ValidationError as e:
    print(str(e))
