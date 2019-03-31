from typing import List

from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError

class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

print(SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes'))
# > SimpleModel password=SecretStr('**********') password_bytes=SecretBytes('**********')


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
