from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class SimpleModel(BaseModel):
    field1: str
    field2: int
    field3: float


class NestedModel(BaseModel):
    field1: str
    field2: List[int]
    field3: Dict[str, float]


class OuterModel(BaseModel):
    nested: NestedModel
    optional_nested: Optional[NestedModel]


class ComplexModel(BaseModel):
    field1: Union[str, int, float]
    field2: List[Dict[str, Union[int, float]]]
    field3: Optional[List[Union[str, int]]]
