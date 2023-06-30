"""
See https://github.com/pydantic/pydantic/issues/4457
"""

from typing import Dict, List

from pydantic import BaseModel, Field


def new_list() -> List[int]:
    return []


class Model(BaseModel):
    l1: List[str] = Field(default_factory=list)
    l2: List[int] = Field(default_factory=new_list)
    l3: List[str] = Field(default_factory=lambda: list())
    l4: Dict[str, str] = Field(default_factory=dict)
    l5: int = Field(default_factory=lambda: 123)
    l6_error: List[str] = Field(default_factory=new_list)
# MYPY: error: Incompatible types in assignment (expression has type "List[int]", variable has type "List[str]")  [assignment]
    l7_error: int = Field(default_factory=list)
# MYPY: error: Incompatible types in assignment (expression has type "List[Any]", variable has type "int")  [assignment]
