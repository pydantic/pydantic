from pydantic import BaseModel, ValidationError, validator

class Model(BaseModel):
    foo: str

    @validator('foo')
    def name_must_contain_space(cls, v):
        if v != 'bar':
            raise ValueError('value must be "bar"')

        return v

try:
    Model(foo='ber')
except ValidationError as e:
    print(e.errors())

"""
[
    {
        'loc': ('foo',),
        'msg': 'value must be "bar"',
        'type': 'value_error',
    },
]
"""
