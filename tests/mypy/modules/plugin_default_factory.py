"""
See https://github.com/pydantic/pydantic/issues/4457
"""


from pydantic import BaseModel, Field


def new_list() -> list[int]:
    return []


class Model(BaseModel):
    l1: list[str] = Field(default_factory=list)
    l2: list[int] = Field(default_factory=new_list)
    l3: list[str] = Field(default_factory=lambda: list())
    l4: dict[str, str] = Field(default_factory=dict)
    l5: int = Field(default_factory=lambda: 123)
    l6_error: list[str] = Field(default_factory=new_list)
    l7_error: int = Field(default_factory=list)
