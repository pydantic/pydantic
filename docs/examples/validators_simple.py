from pydantic import BaseModel, ValidationError, validator


class UserModel(BaseModel):
    name: str
    password1: str
    password2: str

    @validator('name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('passwords do not match')
        return v


print(UserModel(name='samuel colvin', password1='zxcvbn', password2='zxcvbn'))
# > UserModel name='Samuel Colvin' password1='zxcvbn' password2='zxcvbn'

try:
    UserModel(name='samuel', password1='zxcvbn', password2='zxcvbn2')
except ValidationError as e:
    print(e)
"""
2 errors validating input
name:
  must contain a space (error_type=ValueError track=str)
password2:
  passwords do not match (error_type=ValueError track=str)
"""
