---
description: Support for secret types.
---

`SecretBytes`
: bytes where the value is kept partially secret

`SecretStr`
: string where the value is kept partially secret

You can use the `SecretStr` and the `SecretBytes` data types for storing sensitive information
that you do not want to be visible in logging or tracebacks.
`SecretStr` and `SecretBytes` can be initialized idempotently or by using `str` or `bytes` literals respectively.
The `SecretStr` and `SecretBytes` will be formatted as either `'**********'` or `''` on conversion to json.

```py
from pydantic import (
    BaseModel,
    SecretBytes,
    SecretStr,
    ValidationError,
    field_serializer,
)


class SimpleModel(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes


sm = SimpleModel(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')

# Standard access methods will not display the secret
print(sm)
#> password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(sm.password)
#> **********
print(sm.model_dump())
"""
{
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
}
"""
print(sm.model_dump_json())
#> {"password":"**********","password_bytes":"**********"}

# Use get_secret_value method to see the secret's content.
print(sm.password.get_secret_value())
#> IAmSensitive
print(sm.password_bytes.get_secret_value())
#> b'IAmSensitiveBytes'

try:
    SimpleModel(password=[1, 2, 3], password_bytes=[1, 2, 3])
except ValidationError as e:
    print(e)
    """
    2 validation errors for SimpleModel
    password
      Input should be a valid string [type=string_type, input_value=[1, 2, 3], input_type=list]
    password_bytes
      Input should be a valid bytes [type=bytes_type, input_value=[1, 2, 3], input_type=list]
    """


# If you want the secret to be dumped as plain-text using the json method,
# you can use a serializer
class SimpleModelDumpable(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    @field_serializer('password', 'password_bytes', when_used='json')
    def dump_secret(self, v):
        return v.get_secret_value()


sm2 = SimpleModelDumpable(
    password='IAmSensitive', password_bytes=b'IAmSensitiveBytes'
)

# Standard access methods will not display the secret
print(sm2)
#> password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(sm2.password)
#> **********
print(sm2.model_dump())
"""
{
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
}
"""

# But the json method will
print(sm2.model_dump_json())
#> {"password":"IAmSensitive","password_bytes":"IAmSensitiveBytes"}
```
