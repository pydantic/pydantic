"""
Test from_orm check does not raise pydantic-orm error on v1.BaseModel subclass
"""

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.v1 import BaseModel as BaseModelV1


@dataclass
class CustomObject:
    x: int
    y: Optional[int]


obj = CustomObject(x=1, y=2)


class CustomModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        strict=True,
    )

    x: int


cm = CustomModel.from_orm(obj)


class CustomModelV1(BaseModelV1):
    class Config:
        orm_mode = True
        strict = True

    x: int


cmv1 = CustomModelV1.from_orm(obj)
