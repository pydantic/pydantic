from pydantic import BaseModel, Field


class Model(BaseModel):
    a: int
    b: int = ...
    c: int = Field(...)
