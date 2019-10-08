from typing import ClassVar, List, Union

from typing_extensions import Literal

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
#> Cake
print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
#> IceCream
try:
    Meal(dessert={'kind': 'pie'})
except ValidationError as e:
    print(str(e))
"""
2 validation errors
dessert -> kind
  unexpected value; permitted: 'cake' (type=value_error.const; given=pie; permitted=('cake',))
dessert -> kind
  unexpected value; permitted: 'icecream' (type=value_error.const; given=pie; permitted=('icecream',))
"""
