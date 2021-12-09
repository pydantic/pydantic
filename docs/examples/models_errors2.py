from pydantic import BaseModel, ValidationError, validator


class Model(BaseModel):
    foo: str

    @validator('foo')
    def value_must_equal_bar(cls, v):
        if v != 'bar':
            raise ValueError('value must be "bar"')

        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e.errors())
