from pydantic import BaseModel, ValidationError


class StrictStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError(f'strict string: str expected not {type(v)}')
        return v


class Model(BaseModel):
    s: StrictStr


print(Model(s='hello'))
# > Model s='hello'

try:
    print(Model(s=123))
except ValidationError as e:
    print(e.json())
"""
[
  {
    "loc": [
      "s"
    ],
    "msg": "strict string: str expected not <class 'int'>",
    "type": "value_error"
  }
]
"""
