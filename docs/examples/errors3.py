from pydantic import BaseModel, PydanticValueError, ValidationError, validator


class NotABarError(PydanticValueError):
    code = 'not_a_bar'
    msg_template = 'value is not a "bar", got "{wrong_value}"'

    def __init__(self, *, wrong_value: int) -> None:
        super().__init__(wrong_value=wrong_value)


class Model(BaseModel):
    foo: str

    @validator('foo')
    def name_must_contain_space(cls, v):
        if v != 'bar':
            raise NotABarError(wrong_value=v)

        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e.json())
"""
[
  {
    "ctx": {
      "wrong_value": "ber"
    },
    "loc": [
      "foo"
    ],
    "msg": "value is not a \"bar\", got \"ber\"",
    "type": "value_error.not_a_bar"
  }
]
"""
