from pydantic import BaseModel, ValidationError, validator


class UserModel(BaseModel):
    name: str
    username: str
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

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalpha(), 'must be alphanumeric'
        return v


print(UserModel(name='samuel colvin', username='scolvin', password1='zxcvbn', password2='zxcvbn'))
# > UserModel name='Samuel Colvin' password1='zxcvbn' password2='zxcvbn'

try:
    UserModel(name='samuel', username='scolvin', password1='zxcvbn', password2='zxcvbn2')
except ValidationError as e:
    print(e)
"""
2 validation errors
name
  must contain a space (type=value_error)
password2
  passwords do not match (type=value_error)
"""
