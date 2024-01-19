!!! warning "🚧 Work in Progress"
    This page is a work in progress.

## Serialize `SecretStr`, `SecretBytes` and `SecretDate` as plain-text

By default, [`SecretStr`][pydantic.types.SecretStr], [`SecretBytes`][pydantic.types.SecretBytes]
will be serialized as `**********` and [`SecretDate`][pydantic.types.SecretDate] to `****/**/**` when serializing to json.

You can use the [`field_serializer`][pydantic.functional_serializers.field_serializer] to dump the
secret as plain-text when serializing to json.

```py
from pydantic import (
    BaseModel,
    SecretBytes,
    SecretDate,
    SecretStr,
    field_serializer,
)


class Model(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes
    date_of_birth: SecretDate

    @field_serializer(
        'password', 'password_bytes', 'date_of_birth', when_used='json'
    )
    def dump_secret(self, v):
        return v.get_secret_value()


model = Model(
    password='IAmSensitive',
    password_bytes=b'IAmSensitiveBytes',
    date_of_birth='2017-01-01',
)
print(model)
"""
password=SecretStr('**********') password_bytes=SecretBytes(b'**********') date_of_birth=SecretDate('****/**/**')
"""
print(model.password)
#> **********
print(model.password_bytes)
#> b'**********'
print(model.date_of_birth)
#> ****/**/**
print(model.model_dump())
"""
{
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
    'date_of_birth': SecretDate('****/**/**'),
}
"""
print(model.model_dump_json())
"""
{"password":"IAmSensitive","password_bytes":"IAmSensitiveBytes","date_of_birth":"2017-01-01"}
"""
```
