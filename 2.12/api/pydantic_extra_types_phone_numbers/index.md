The `pydantic_extra_types.phone_numbers` module provides the PhoneNumber data type.

This class depends on the [phonenumbers] package, which is a Python port of Google's [libphonenumber].

## PhoneNumber

Bases: `str`

A wrapper around [phonenumbers](https://pypi.org/project/phonenumbers/) package, which is a Python port of Google's [libphonenumber](https://github.com/google/libphonenumber/).

### supported_regions

```python
supported_regions: list[str] = []

```

The supported regions. If empty, all regions are supported.

### default_region_code

```python
default_region_code: str | None = None

```

The default region code to use when parsing phone numbers without an international prefix.

### phone_format

```python
phone_format: str = 'RFC3966'

```

The format of the phone number.

## PhoneNumberValidator

```python
PhoneNumberValidator(
    default_region: Optional[str] = None,
    number_format: str = "RFC3966",
    supported_regions: Optional[Sequence[str]] = None,
)

```

A pydantic before validator for phone numbers using the [phonenumbers](https://pypi.org/project/phonenumbers/) package, a Python port of Google's [libphonenumber](https://github.com/google/libphonenumber/).

Intended to be used to create custom pydantic data types using the `typing.Annotated` type construct.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `default_region` | `str | None` | The default region code to use when parsing phone numbers without an international prefix. If None (default), the region must be supplied in the phone number as an international prefix. | `None` | | `number_format` | `str` | The format of the phone number to return. See phonenumbers.PhoneNumberFormat for valid values. | `'RFC3966'` | | `supported_regions` | `list[str]` | The supported regions. If empty, all regions are supported (default). | `None` |

Returns: str: The formatted phone number.

Example

MyNumberType = Annotated\[ Union[str, phonenumbers.PhoneNumber], PhoneNumberValidator() \] USNumberType = Annotated\[ Union[str, phonenumbers.PhoneNumber], PhoneNumberValidator(supported_regions=['US'], default_region='US') \]

class SomeModel(BaseModel): phone_number: MyNumberType us_number: USNumberType
