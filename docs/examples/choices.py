from enum import Enum, IntEnum

from pydantic import BaseModel


class FruitEnum(str, Enum):
    pear = 'pear'
    banana = 'banana'


class ToolEnum(IntEnum):
    spanner = 1
    wrench = 2


class CookingModel(BaseModel):
    fruit: FruitEnum = FruitEnum.pear
    tool: ToolEnum = ToolEnum.spanner


print(CookingModel())
#> CookingModel fruit=<FruitEnum.pear: 'pear'> tool=<ToolEnum.spanner: 1>
print(CookingModel(tool=2, fruit='banana'))
#> CookingModel fruit=<FruitEnum.banana: 'banana'> tool=<ToolEnum.wrench: 2>
print(CookingModel(fruit='other'))
# will raise a validation error
