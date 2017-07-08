from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    v: str

    class Config:
        max_anystr_length = 10


try:
    Model(v='x' * 20)
except ValidationError as e:
    print(e)
"""
error validating input
v:
  length not in range 0 to 10 (error_type=ValueError track=str)
"""
