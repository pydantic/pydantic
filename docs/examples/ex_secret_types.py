from typing import List

from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError

class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm)
#> SimpleModel password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(str(sm.password.display))
#> '**********'
print(sm.json())
#> '{"password": "**********", "password_bytes": "**********"}'

# Use get_secret_value method to see the secret's content.
print(sm.password.get_secret_value())
#> IAmSensitive
print(sm.password_bytes.get_secret_value())
#> b'IAmSensitiveBytes'


try:
    SimpleModel(password=[1,2,3], password_bytes=[1,2,3])
except ValidationError as e:
    print(e)
"""
2 validation error
password
  str type expected (type=type_error.str)
password_bytes
  byte type expected (type=type_error.bytes)
"""
