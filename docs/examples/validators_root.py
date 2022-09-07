from pydantic import BaseModel, ValidationError, root_validator


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str

    @root_validator(pre=True)
    def check_card_number_omitted(cls, values):
        assert 'card_number' not in values, 'card_number should not be included'
        return values

    @root_validator
    def check_passwords_match(cls, values):
        pw1, pw2 = values.get('password1'), values.get('password2')
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return values


print(UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn'))
try:
    UserModel(username='scolvin', password1='zxcvbn', password2='zxcvbn2')
except ValidationError as e:
    print(e)

try:
    UserModel(
        username='scolvin',
        password1='zxcvbn',
        password2='zxcvbn',
        card_number='1234',
    )
except ValidationError as e:
    print(e)
