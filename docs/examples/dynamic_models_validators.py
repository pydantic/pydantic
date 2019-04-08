from pydantic import ValidationError, create_model, validator

@validator('name')
def name_must_contain_space(v):
    if ' ' not in v:
        raise ValueError('must contain a space')
    return v.title()

@validator('password2')
def passwords_match(v, values, **kwargs):
    if 'password1' in values and v != values['password1']:
        raise ValueError('passwords do not match')
    return v

DynamicUserModel = create_model(
    'DynamicUserModel',
    __validators__=[name_must_contain_space, passwords_match],
    name=(str, ...),
    password1=(str, ...),
    password2=(str, ...),
)

try:
    DynamicUserModel(name='YouName', password1=123, password2=456)
except ValidationError as e:
    print(e)

"""
2 validation errors
name
  must contain a space (type=value_error)
password2
  passwords do not match (type=value_error)
"""
