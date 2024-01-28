!!! warning "🚧 Work in Progress"
    This page is a work in progress.

## Serialize `SecretStr` and `SecretBytes` as plain-text

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

## Create your own Secret field
It is possible to create your own secret field. To do this inherit from the Generic Secret class with your underlying type.
Overwrite the `_display` method to choose the string representation.

```py
from datetime import date

from pydantic import BaseModel, Secret

# Using the default representation
SecretDate = Secret[date]


# Overwriting the representation
class SecretSalary(Secret[float]):
    def _display(self) -> str:
        return '$****.**'


class Employee(BaseModel):
    date_of_birth: SecretDate
    salary: SecretSalary


employee = Employee(date_of_birth='1990-01-01', salary=42)

print(employee)
#> date_of_birth=Secret('**********') salary=SecretSalary('$****.**')

print(employee.salary)
#> $****.**

print(employee.salary.get_secret_value())
#> 42.0

print(employee.date_of_birth)
#> **********

print(employee.date_of_birth.get_secret_value())
#> 1990-01-01
```

To make a secret field reveal the data while serializing to JSON, you can use a `PlainSerializer`

```py
from datetime import date

from typing_extensions import Annotated

from pydantic import PlainSerializer, Secret


class _SecretDate(Secret[date]):
    def _display(self) -> str:
        return '****/**/**'


SecretDate = Annotated[
    _SecretDate,
    PlainSerializer(
        lambda v: v.get_secret_value().strftime('%Y-%m-%d') if v else None,
        when_used='json',
    ),
]
```

Secrets can't be `Strict`, but the underlying types can.

For example:

```py
from pydantic import Secret, StrictStr

StrictSecretStr = Secret[StrictStr]
```
