!!! warning "🚧 Work in Progress"
    This page is in work in progress.

# Serialize `SecretStr` and `SecretBytes` as plain-text

By default, [`SecretStr`][pydantic.types.SecretStr] and [`SecretBytes`][pydantic.types.SecretBytes]
will be serialized as `**********` when serializing to json.

You can use the [`field_serializer`][pydantic.functional_serializers.field_serializer] to dump the
secret as plain-text when serializing to json.

```py
from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer


class Model(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    @field_serializer('password', 'password_bytes', when_used='json')
    def dump_secret(self, v):
        return v.get_secret_value()


model = Model(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')
print(model)
#> password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(model.password)
#> **********
print(model.model_dump())
"""
{
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
}
"""
print(model.model_dump_json())
#> {"password":"IAmSensitive","password_bytes":"IAmSensitiveBytes"}
```
