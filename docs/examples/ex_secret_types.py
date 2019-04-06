from typing import List

from pydantic import BaseModel, SecretStr, SecretBytes, ValidationError

class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

sm1 = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')
print(sm)
# > SimpleModel password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(sm.password)
# > **********
print(repr(sm.password))
# > SecretStr('**********')
print(sm.password_bytes)
# > **********
print(repr(sm.password_bytes))
# > SecretStr(b'**********')
print(sm.dict())
# > {'password': SecretStr('**********'), 'password_bytes': SecretBytes(b'**********')}
print(sm.json())
# > {"password": "**********", "password_bytes": "**********"}


sm2 = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')
print(sm2.password.get_secret_value())
# > IAmSensitive
print(sm2.password_bytes.get_secret_value())
# > b'IAmSensitiveBytes'


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
