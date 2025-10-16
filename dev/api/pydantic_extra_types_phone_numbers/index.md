The `pydantic_extra_types.phone_numbers` module provides the PhoneNumber data type.

This class depends on the [phonenumbers](https://pypi.orgt/phonenumbers/) package, which is a Python port of Google's [libphonenumber](https://github.com/google/libphonenumber/).

## PhoneNumber

Bases: `str`

A wrapper around the `phonenumbers.PhoneNumber` object.

It provides class-level configuration points you can change by subclassing:

#### Examples

##### Normal usage:

```python
    from pydantic import BaseModel
    from pydantic_extra_types.phone_numbers import PhoneNumber

    class Contact(BaseModel):
        name: str
        phone: PhoneNumber

    c = Contact(name='Alice', phone='+1 650-253-0000')
    print(c.phone)
    >> tel:+1-650-253-0000 (formatted using RFC3966 by default)

```

##### Changing defaults by subclassing:

```python
    from pydantic_extra_types.phone_numbers import PhoneNumber

    class USPhone(PhoneNumber):
        default_region_code = 'US'
        supported_regions = ['US']
        phone_format = 'NATIONAL'

    # Now parsing will accept national numbers for the US
    p = USPhone('650-253-0000')
    print(p)
    >> 650-253-0000

```

##### Changing defaults by using the provided validator annotation:

```python
    from typing import Annotated, Union
    import phonenumbers
    from pydantic import BaseModel
    from pydantic_extra_types.phone_numbers import PhoneNumberValidator

    E164NumberType = Annotated[
        Union[str, phonenumbers.PhoneNumber], PhoneNumberValidator(number_format="E164")
    ]


    class Model(BaseModel):
        phone: E164NumberType


    m = Model(phone="+1 650-253-0000")
    print(m.phone)
    >> +16502530000

```

### default_region_code

```python
default_region_code: str | None = None

```

The default region code to use when parsing phone numbers without an international prefix.

### supported_regions

```python
supported_regions: list[str] = []

```

The supported regions. If empty, all regions are supported.

### phone_format

```python
phone_format: str = 'RFC3966'

```

The format of the phone number.

## PhoneNumberValidator

```python
PhoneNumberValidator(
    default_region: str | None = None,
    number_format: str = "RFC3966",
    supported_regions: Sequence[str] | None = None,
)

```

An annotation to validate `phonenumbers.PhoneNumber` objects.

Example

```python
from typing import Annotated, Union

import phonenumbers
from pydantic import BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

MyNumberType = Annotated[Union[str, phonenumbers.PhoneNumber], PhoneNumberValidator()]

USNumberType = Annotated[
    Union[str, phonenumbers.PhoneNumber], PhoneNumberValidator(supported_regions=['US'], default_region='US')
]


class SomeModel(BaseModel):
    phone_number: MyNumberType
    us_number: USNumberType

```

### default_region

```python
default_region: str | None = None

```

The default region code to use when parsing phone numbers without an international prefix.

If `None` (the default), the region must be supplied in the phone number as an international prefix.

### number_format

```python
number_format: str = 'RFC3966'

```

The format of the phone number to return. See `phonenumbers.PhoneNumberFormat` for valid values.

### supported_regions

```python
supported_regions: Sequence[str] | None = None

```

The supported regions. If empty (the default), all regions are supported.
