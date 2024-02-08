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

Pydantic provides the generic `Secret` class as a mechanism for creating custom secret types.

??? api "API Documentation"
    [`pydantic.types.Secret`][pydantic.types.Secret]<br>

Pydantic provides the generic `Secret` class as a mechanism for creating custom secret types.
You can either directly parametrize `Secret`, or subclass from a parametrized `Secret` to customize the `str()` and `repr()` of a secret type.

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

Pydantic currently supports enforcing constraints on the underlying type of a secret type, but not the secret type itself.
For example:

```py
from typing import Annotated

from pydantic import BaseModel, Field, Secret, ValidationError

SecretPosInt = Secret[Annotated[int, Field(gt=0, strict=True)]]


class Model(BaseModel):
    sensitive_int: SecretPosInt


m = Model(sensitive_int=42)
print(m.model_dump())
#> {'sensitive_int': Secret('**********')}

try:
    m = Model(sensitive_int=-42)  # (1)!
except ValidationError as exc_info:
    print(exc_info.errors(include_url=False, include_input=False))
    """
    [
        {
            'type': 'greater_than',
            'loc': ('sensitive_int',),
            'msg': 'Input should be greater than 0',
            'ctx': {'gt': 0},
        }
    ]
    """

try:
    m = Model(sensitive_int='42')  # (2)!
except ValidationError as exc_info:
    print(exc_info.errors(include_url=False, include_input=False))
    """
    [
        {
            'type': 'int_type',
            'loc': ('sensitive_int',),
            'msg': 'Input should be a valid integer',
        }
    ]
    """
```

1. The input value is not greater than 0, so it raises a validation error.
2. The input value is not an integer, so it raises a validation error because the SecretPOsInt type has strict mode enabled.
