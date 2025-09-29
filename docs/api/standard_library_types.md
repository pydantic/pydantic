---
description: Support for common types from the Python standard library.
---

This section enumerates the supported built-in and standard library types: the allowed values,
the possible constraints, and whether strictness can be configured.

!!! note
    Unless specified otherwise, values are serialized as-is, in both Python and JSON modes.

!!! note
    Pydantic still supports older (3.8-) typing constructs like `typing.List` and `typing.Dict`, but
    it's best practice to use the newer types like `list` and `dict`.

## Booleans

Built-in type: [`bool`][]

<h3>Validation</h3>

* A valid [`bool`][] instance, i.e. `True` or `False`
* The integers `0` or `1`
* A string, which when converted to lowercase is one of `'0'`, `'off'`, `'f'`, `'false'`, `'n'`, `'no'`, `'1'`, `'on'` `'t'`, `'true'`, `'y'`, `'yes'`
* In Python mode, a [`bytes`][] object which is valid per the previous rule when decoded to a string. 

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only boolean values are valid. Pydantic provides the [`StrictBool`][pydantic.types.StrictBool]
type as a convenience to [using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<h3>Example</h3>

```python
from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
#> bool_value=False
print(BooleanModel(bool_value='False'))
#> bool_value=False
print(BooleanModel(bool_value=1))
#> bool_value=True
try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
    """
    1 validation error for BooleanModel
    bool_value
      Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]
    """
```

## Strings

Built-in type: [`str`][]

<h3>Validation</h3>

* Strings are accepted as-is
* [`bytes`][] and [`bytearray`][] are decoded to UTF-8 strings
* [Enums][enum] are converted using the [`value`][enum.Enum.value] attribute, by calling [`str()`][str]
  on it.
* If [`coerce_numbers_to_str`][pydantic.ConfigDict.coerce_numbers_to_str] is set, any number type
  ([`int`][], [`float`][] and [`Decimal`][decimal.Decimal]) will be coerced to a string and accepted
  as-is.

<h3>Constraints</h3>

Strings support the following constraints:

| Constraint         | Description                                       | JSON Schema                                                                                      |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `pattern`          | A regex pattern that the string must match        | [`pattern`](https://json-schema.org/understanding-json-schema/reference/string#regexp) keyword   |
| `min_length`       | The minimum length of the string                  | [`minLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword |
| `max_length`       | The maximum length of the string                  | [`maxLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword |
| `strip_whitespace` | Whether to remove leading and trailing whitespace | N/A                                                                                              |
| `to_upper`         | Whether to convert the string to uppercase        | N/A                                                                                              |
| `to_lower`         | Whether to convert the string to lowercase        | N/A                                                                                              |

These constraints can be provided using the [`StringConstraints`][pydantic.types.StringConstraints] metadata type, or using the [`Field()`][pydantic.Field] function (except for `to_upper` and `to_lower`).
The `MinLen`, `MaxLen`, `Len`, `LowerCase`, `UpperCase` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only string values are valid. Pydantic provides the [`StrictStr`][pydantic.types.StrictStr]
type as a convenience to [using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<h3>Example</h3>

```python
from pydantic import BaseModel, StringConstraints


class StringModel(BaseModel):
    str_value: str = ""
    constrained_str_value: Annotated[str, StringConstraints(to_lower=True)] = ""

print(StringModel(str_value="test").str_value)
#> str_value="test"
print(StringModel(constrained_str_value='TEST').constrained_str_value)
#> constrained_str_value="test"
```

!!! warning "Strings aren't treated as sequences"

    While [`str`][] instances are technically valid [sequence][] instances, this is frequently not intended as is a common source of bugs.

    As a result, Pydantic will *not* accept
     raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type
    `Sequence[str]` or `Sequence[bytes]`:


```python
from collections.abc import Sequence
from typing import Optional

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    sequence_of_strs: Optional[Sequence[str]] = None
    sequence_of_bytes: Optional[Sequence[bytes]] = None


print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
#> ['a', 'bc']
print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
#> ('a', 'bc')
print(Model(sequence_of_bytes=[b'a', b'bc']).sequence_of_bytes)
#> [b'a', b'bc']
print(Model(sequence_of_bytes=(b'a', b'bc')).sequence_of_bytes)
#> (b'a', b'bc')


try:
    Model(sequence_of_strs='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_strs
      'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
    """
try:
    Model(sequence_of_bytes=b'abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_bytes
      'bytes' instances are not allowed as a Sequence value [type=sequence_str, input_value=b'abc', input_type=bytes]
    """
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#number-types}
## Numbers

Pydantic supports the following numeric types from the Python standard library:

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#int}
### Integers

Built-in type: [`int`][].

<h4>Validation</h4>

* Integers are validated as-is
* Strings and bytes are attempted to be converted to integers and validated as-is
  (see the [jiter implementation](https://docs.rs/jiter/latest/jiter/enum.NumberInt.html#impl-TryFrom%3C%26%5Bu8%5D%3E-for-NumberInt) for details)
* Floats are validated as integers, provided the float input is not infinite or a NaN (not-a-number)
  and the fractional part is 0
* [`Decimal`][decimal.Decimal] instances, provided they are [finite][decimal.Decimal.is_finite] and the
  denominator is 1
* [`Fraction`][fractions.Fraction] instances, provided they are [integers][fractions.Fraction.is_integer].
* [Enums][enum] are converted using the [`value`][enum.Enum.value] attribute.

<h4>Constraints</h4>

Integers support the following constraints (numbers must be coercible to integers):

| Constraint    | Description                                            | JSON Schema                                                                                             |
| ------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `le`          | The value must be less than or equal to this number    | [`maximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword          |
| `ge`          | The value must be greater than or equal to this number | [`minimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword          |
| `lt`          | The value must be strictly less than this number       | [`exclusiveMaximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword |
| `gt`          | The value must be strictly greater than this number    | [`exclusiveMinimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword |
| `multiple_of` | The value must be a multiple of this number            | [`multipleOf`](https://json-schema.org/understanding-json-schema/reference/numeric#multiples) keyword   |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt`, `Gt` and `MultipleOf` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

Pydantic also provides the following types to further constrain the allowed integer values:

* [`PositiveInt`][pydantic.types.PositiveInt]: Requires the input to be greater than zero.
* [`NegativeInt`][pydantic.types.NegativeInt]: Requires the input to be less than zero.
* [`NonPositiveInt`][pydantic.types.NonPositiveInt]: Requires the input to be less than or equal to zero.
* [`NonNegativeInt`][pydantic.types.NonNegativeInt]: Requires the input to be greater than or equal to zero.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only integer values are valid. Pydantic provides the [`StrictInt`][pydantic.types.StrictInt]
type as a convenience to [using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#float}
### Floats

Built-in type: [`float`][].

<h4>Validation</h4>

* Floats are validated as-is
* String and bytes are attempted to be converted to floats and validated as-is
  (see the [Rust implementation](https://doc.rust-lang.org/src/core/num/dec2flt/mod.rs.html) for details)
* If the input has a [`__float__()`][object.__float__] method, it will be called to convert the input into
  a float. If `__float__()` is not defined, it falls back to [`__index__()`][object.__index__]. This includes
  (but not limited to) the [`Decimal`][decimal.Decimal] and [`Fraction`][fractions.Fraction] types.

<h4>Constraints</h4>

Floats support the following constraints:

| Constraint      | Description                                             | JSON Schema                                                                                             |
| --------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `le`            | The value must be less than or equal to this number     | [`maximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword          |
| `ge`            | The value must be greater than or equal to this number  | [`minimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword          |
| `lt`            | The value must be strictly less than this number        | [`exclusiveMaximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword |
| `gt`            | The value must be strictly greater than this number     | [`exclusiveMinimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword |
| `multiple_of`   | The value must be a multiple of this number             | [`multipleOf`](https://json-schema.org/understanding-json-schema/reference/numeric#multiples) keyword   |
| `allow_inf_nan` | Whether to allow NaN (not-a-number) and infinite values | N/A                                                                                                     |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt`, `Gt` and `MultipleOf` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library and the [`AllowInfNan`][pydantic.types.AllowInfNan] type can also be used.

Pydantic also provides the following types to further constrain the allowed float values:

* [`PositiveFloat`][pydantic.types.PositiveFloat]: Requires the input to be greater than zero.
* [`NegativeFloat`][pydantic.types.NegativeFloat]: Requires the input to be less than zero.
* [`NonPositiveFloat`][pydantic.types.NonPositiveFloat]: Requires the input to be less than or equal to zero.
* [`NonNegativeFloat`][pydantic.types.NonNegativeFloat]: Requires the input to be greater than or equal to zero.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only float values and inputs having a [`__float__()`][object.__float__]
or [`__index__()`][object.__index__] method are valid.
Pydantic provides the [`StrictFloat`][pydantic.types.StrictFloat] type as a convenience to
[using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#enum.IntEnum}
### Integer enums

Standard library type: [`enum.IntEnum`][].

<h4>Validation</h4>

* If the [`enum.IntEnum`][] type is used directly, any [`enum.IntEnum`][] instance is validated as-is
* Id an [`enum.IntEnum`][] subclass is used as a type, any enum member or value that correspond to the
  enum members values is validated as-is.

See [Enums](#enums) for more details.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#decimal.Decimal}
### Decimals

Standard library type: [`decimal.Decimal`][].

<h4>Validation</h4>

* [`Decimal`][decimal.Decimal] instances are validated as is
* Any value accepted by the [`Decimal`][decimal.Decimal] constructor (apart from the
  three-tuple input) will validate.

<h4>Constraints</h4>

Decimals support the following constraints (numbers must be coercible to decimals):

| Constraint       | Description                                                                                                         | JSON Schema                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `le`             | The value must be less than or equal to this number                                                                 | [`maximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword                                 |
| `ge`             | The value must be greater than or equal to this number                                                              | [`minimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword                                 |
| `lt`             | The value must be strictly less than this number                                                                    | [`exclusiveMaximum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword                        |
| `gt`             | The value must be strictly greater than this number                                                                 | [`exclusiveMinimum`](https://json-schema.org/understanding-json-schema/reference/numeric#range) keyword                        |
| `multiple_of`    | The value must be a multiple of this number                                                                         | [`multipleOf`](https://json-schema.org/understanding-json-schema/reference/numeric#multiples) keyword                          |
| `allow_inf_nan`  | Whether to allow NaN (not-a-number) and infinite values                                                             | N/A                                                                                                                            |
| `max_digits`     | The maximum number of decimal digits allowed. The zero before the decimal point and trailing zeros are not counted. | [`pattern`](https://json-schema.org/understanding-json-schema/reference/string#regexp) keyword, to describe the string pattern |
| `decimal_places` | The maximum number of decimal places allowed. Trailing zeros are not counted.                                       | [`pattern`](https://json-schema.org/understanding-json-schema/reference/string#regexp) keyword, to describe the string pattern |

Note that the JSON Schema [`pattern`](https://json-schema.org/understanding-json-schema/reference/string#regexp) keyword will be specified
in the JSON Schema to describe the string pattern in all cases (and can vary if `max_digits` and/or `decimal_places` is specified).

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt`, `Gt` and `MultipleOf` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library and the [`AllowInfNan`][pydantic.types.AllowInfNan] type can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`decimal.Decimal`][] instances are accepted. In JSON mode, strict mode has no effect.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`Decimal`][decimal.Decimal] instances are 
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.
A [serializer](../concepts/serialization.md#field-plain-serializer) can be used to override this behavior:

```python
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer


class Model(BaseModel):
    f: Annotated[Decimal, PlainSerializer(float, when_used='json')]


my_model = Model(f=Decimal('2.1'))

print(my_model.model_dump())  # (1)!
#> {'f': Decimal('2.1')}
print(my_model.model_dump_json())  # (2)!
#> '{"f":2.1}'
```

1. In Python mode, `f`remains a [`Decimal`][decimal.Decimal] instance.
2. In JSON mode, `f` is serialized as a float.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#complex}
### Complex numbers

Built-in type: [`complex`][].

<h4>Validation</h4>

* [`complex`][] instances are validated as-is
* Strings are validated using the [`complex()`][complex] constructor
* Numbers (integers and floats) are used as the real part
* Objects defining [`__complex__()`][object.__complex__], [`__float__()`][object.__float__]
  or [`__index__()`][object.__index__] are currently *not* accepted.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`complex`][] instances are accepted. In JSON mode, only strings that are
accepted by the [`complex()`][complex] constructor are allowed.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`Decimal`][decimal.Decimal] instances are 
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#fractions.Fraction}
### Fractions

Standard library type: [`fractions.Fraction`][].

<h4>Validation</h4>

* [`Fraction`][fractions.Fraction] instances are validated as is
* Floats, strings and [`decimal.Decimal`][] instances are validated using the [`Fraction()`][fractions.Fraction]
  constructor.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`Fraction`][fractions.Fraction] instances are accepted. In JSON mode, strict mode has no effect.

<h4>Serialization</h4>

Fractions are serialized as strings, both in [Python](../concepts/serialization.md#python-mode)
and [JSON](../concepts/serialization.md#json-mode) modes.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetime-types}
## Date and time types

Pydantic supports the following [date and time](https://docs.python.org/library/datetime.html#available-types)
types from the [`datetime`][] standard library:

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetime.datetime}
### Datetimes

Standard library type: [`datetime.datetime`][].

<h4>Validation</h4>

* [`datetime`][datetime.datetime] instances are validated as is.
* Strings and bytes are validated in two ways:
    * Strings complying to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format (both datetime and date).
      See the [speedate](https://docs.rs/speedate/) documentation for more details.
    * Unix timestamps, both as seconds or miliseconds sinch the [epoch](https://en.wikipedia.org/wiki/Unix_time).
      See the [`val_temporal_unit`][pydantic.ConfigDict.val_temporal_unit] configuration value for more details.
* Integers and floats (or types that can be coerced as integers or floats) are validated as unix timestamps, following the
  same semantics as strings.
* [`datetime.date`][] instances are accepted, and converted to a [`datetime`][datetime.datetime] instance
  by setting the [`hour`][datetime.datetime.hour], [`minute`][datetime.datetime.minute], [`second`][datetime.datetime.second] and
  [`microsecond`][datetime.datetime.microsecond] attributes to `0`, and the [`tzinfo`][datetime.datetime.tzinfo] attribute to `None`.

<h4>Constraints</h4>

Datetimes support the following constraints (constraint values must be coercible to a [`datetime`][datetime.datetime] instance):

| Constraint | Description                                              | JSON Schema |
| ---------- | -------------------------------------------------------- | ----------- |
| `le`       | The value must be less than or equal to this datetime    | N/A         |
| `ge`       | The value must be greater than or equal to this datetime | N/A         |
| `lt`       | The value must be strictly less than this datetime       | N/A         |
| `gt`       | The value must be strictly greater than this datetime    | N/A         |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt` and `Gt` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

Pydantic also provides the following types to further constrain the allowed datetime values:

* [`AwareDatetime`][pydantic.types.AwareDatetime]: Requires the input to have a timezone.
* [`NaiveDatetime`][pydantic.types.NaiveDatetime]: Requires the input to *not* have a timezone.
* [`PastDatetime`][pydantic.types.PastDatetime]: Requires the input to be in the past when validated.
* [`FutureDatetime`][pydantic.types.FutureDatetime]: Requires the input to be in the future when validated.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`datetime`][datetime.datetime] instances are accepted. In JSON mode, only strings complying to the
[RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format (*only* datetime) or as unix timestamps are accepted.

<h4>Example</h4>

```python
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field


class Event(BaseModel):
    dt: Annotated[AwareDatetime, Field(gt=datetime(2000, 1, 1))]


event = Event(dt='2032-04-23T10:20:30.400+02:30')

print(event.model_dump())
"""
{'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(9000))}
"""
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetime.date}
### Dates

Standard library type: [`datetime.date`][].

<h4>Validation</h4>

* [`date`][datetime.date] instances are validated as is.
* Strings and bytes are validated in two ways:
    * Strings complying to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) date format.
      See the [speedate](https://docs.rs/speedate/) documentation for more details.
    * Unix timestamps, both as seconds or miliseconds sinch the [epoch](https://en.wikipedia.org/wiki/Unix_time).
      See the [`val_temporal_unit`][pydantic.ConfigDict.val_temporal_unit] configuration value for more details.
* If the validation fails, the input can be [validated as a datetime](#datetimes) (including as numbers),
  provided that the time component is 0 and that it is naive.

<h4>Constraints</h4>

Dates support the following constraints (constraint values must be coercible to a [`date`][datetime.date] instance):

| Constraint | Description                                          | JSON Schema |
| ---------- | ---------------------------------------------------- | ----------- |
| `le`       | The value must be less than or equal to this date    | N/A         |
| `ge`       | The value must be greater than or equal to this date | N/A         |
| `lt`       | The value must be strictly less than this date       | N/A         |
| `gt`       | The value must be strictly greater than this date    | N/A         |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt` and `Gt` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

Pydantic also provides the following types to further constrain the allowed date values:

* [`PastDate`][pydantic.types.PastDate]: Requires the input to be in the past when validated.
* [`FutureDate`][pydantic.types.FutureDate]: Requires the input to be in the future when validated.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`date`][datetime.date] instances are accepted. In JSON mode, only strings complying to the
[RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format (*only* date) or as unix timestamps are accepted.

<h4>Example</h4>

```python
from datetime import date

from pydantic import BaseModel


class Birthday(BaseModel):
    d: date


my_birthday = Birthday(d=1679616000.0)

print(my_birthday.model_dump())
#> {'d': datetime.date(2023, 3, 24)}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetime.time}
### Time

Standard library type: [`datetime.time`][].

<h4>Validation</h4>

* [`time`][datetime.time] instances are validated as is.
* Strings and bytes are validated according to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) time format.
* Integers and floats (or values that can be coerced to such numbers) are validated as seconds. The value should not exceed 86 399.

<h4>Constraints</h4>

Time support the following constraints (constraint values must be coercible to a [`time`][datetime.time] instance):

| Constraint | Description                                          | JSON Schema |
| ---------- | ---------------------------------------------------- | ----------- |
| `le`       | The value must be less than or equal to this time    | N/A         |
| `ge`       | The value must be greater than or equal to this time | N/A         |
| `lt`       | The value must be strictly less than this time       | N/A         |
| `gt`       | The value must be strictly greater than this time    | N/A         |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt` and `Gt` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`time`][datetime.time] instances are accepted. In JSON mode, only strings complying to the
[RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format are accepted.

<h4>Example</h4>

```python
from datetime import time

from pydantic import BaseModel


class Meeting(BaseModel):
    t: time


m = Meeting(t=time(4, 8, 16))

print(m.model_dump())
#> {'t': datetime.time(4, 8, 16)}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetime.timedelta}
### Timedeltas

Standard library type: [`datetime.timedelta`][].

<h4>Validation</h4>

* [`timedelta`][datetime.timedelta] instances are validated as is.
* Strings and bytes are validated according to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) time format.
* Integers and floats (or values that can be coerced to such numbers) are validated as seconds.

<h4>Constraints</h4>

Timedeltas support the following constraints (constraint values must be coercible to a [`timedata`][datetime.timedelta] instance):

| Constraint | Description                                               | JSON Schema |
| ---------- | ---------------------------------------------------- -----| ----------- |
| `le`       | The value must be less than or equal to this timedelta    | N/A         |
| `ge`       | The value must be greater than or equal to this timedelta | N/A         |
| `lt`       | The value must be strictly less than this timedelta       | N/A         |
| `gt`       | The value must be strictly greater than this timedelta    | N/A         |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `Le`, `Ge`, `Lt` and `Gt` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`timedelta`][datetime.timedelta] instances are accepted. In JSON mode, only strings complying to the
[RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format are accepted.

<h4>Example</h4>

```python
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    td: timedelta


m = Model(td='P3DT12H30M5S')

print(m.model_dump())
#> {'td': datetime.timedelta(days=3, seconds=45005)}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#enum.enum}
## Enums

Standard library type: [`enum.Enum`][].

<h3>Validation</h3>

* If the [`enum.Enum`][] type is used directly, any [`enum.Enum`][] instance is validated as-is
* Id an [`enum.Enum`][] subclass is used as a type, any enum member or value that correspond to the
  enum members values is validated as-is.

<h3>Example</h3>

```python
from enum import Enum, IntEnum

from pydantic import BaseModel, ValidationError


class FruitEnum(str, Enum):
    PEAR = 'pear'
    BANANA = 'banana'


class ToolEnum(IntEnum):
    SPANNER = 1
    WRENCH = 2


class CookingModel(BaseModel):
    fruit: FruitEnum = FruitEnum.PEAR
    tool: ToolEnum = ToolEnum.SPANNER


print(CookingModel())
#> fruit=<FruitEnum.PEAR: 'pear'> tool=<ToolEnum.SPANNER: 1>
print(CookingModel(tool=2, fruit='banana'))
#> fruit=<FruitEnum.BANANA: 'banana'> tool=<ToolEnum.WRENCH: 2>
try:
    CookingModel(fruit='other')
except ValidationError as e:
    print(e)
    """
    1 validation error for CookingModel
    fruit
      Input should be 'pear' or 'banana' [type=enum, input_value='other', input_type=str]
    """
```

## Lists and Tuples

### [`list`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`list`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the list.

```python
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_list: Optional[list] = None
    list_of_ints: Optional[list[int]] = None


print(Model(simple_list=['1', '2', '3']).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
#> [1, 2, 3]
```

### [`tuple`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`tuple`][].
When generic parameters are provided, the appropriate validation is applied to the respective items of the tuple

### [`typing.Tuple`][]

Handled the same as `tuple` above.

```python
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_tuple: Optional[tuple] = None
    tuple_of_different_types: Optional[tuple[int, float, bool]] = None


print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
#> (1, 2, 3, 4)
print(Model(tuple_of_different_types=[3, 2, 1]).tuple_of_different_types)
#> (3, 2.0, True)
```

### [`typing.NamedTuple`][]

Subclasses of [`typing.NamedTuple`][] are similar to `tuple`, but create instances of the given `namedtuple` class.

Subclasses of [`collections.namedtuple`][] are similar to subclass of [`typing.NamedTuple`][], but since field types are not specified,
all fields are treated as having type [`Any`][typing.Any].

```python
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
    """
```

## Deque

### [`deque`][collections.deque]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`deque`][collections.deque].
When generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`.

### [`typing.Deque`][]

Handled the same as `deque` above.

```python {lint="skip"}
from typing import Deque, Optional

from pydantic import BaseModel


class Model(BaseModel):
    deque: Optional[Deque[int]] = None


print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

## Sets

### [`set`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`set`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the set.

### [`typing.Set`][]

Handled the same as `set` above.

```python {lint="skip"}
from typing import Optional, Set

from pydantic import BaseModel


class Model(BaseModel):
    simple_set: Optional[set] = None
    set_of_ints: Optional[Set[int]] = None


print(Model(simple_set={'1', '2', '3'}).simple_set)
#> {'1', '2', '3'}
print(Model(simple_set=['1', '2', '3']).simple_set)
#> {'1', '2', '3'}
print(Model(set_of_ints=['1', '2', '3']).set_of_ints)
#> {1, 2, 3}
```

### [`frozenset`][]

Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`frozenset`][].
When a generic parameter is provided, the appropriate validation is applied to all items of the frozen set.

### [`typing.FrozenSet`][]

Handled the same as `frozenset` above.

```python {lint="skip"}
from typing import FrozenSet, Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_frozenset: Optional[frozenset] = None
    frozenset_of_ints: Optional[FrozenSet[int]] = None


m1 = Model(simple_frozenset=['1', '2', '3'])
print(type(m1.simple_frozenset))
#> <class 'frozenset'>
print(sorted(m1.simple_frozenset))
#> ['1', '2', '3']

m2 = Model(frozenset_of_ints=['1', '2', '3'])
print(type(m2.frozenset_of_ints))
#> <class 'frozenset'>
print(sorted(m2.frozenset_of_ints))
#> [1, 2, 3]
```

## Other Iterables

### [`typing.Sequence`][]

This is intended for use when the provided value should meet the requirements of the `Sequence` ABC, and it is
desirable to do eager validation of the values in the container. Note that when validation must be performed on the
values of the container, the type of the container may not be preserved since validation may end up replacing values.
We guarantee that the validated value will be a valid [`typing.Sequence`][], but it may have a different type than was
provided (generally, it will become a `list`).

### [`typing.Iterable`][]

This is intended for use when the provided value may be an iterable that shouldn't be consumed.
See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation.
Similar to [`typing.Sequence`][], we guarantee that the validated result will be a valid [`typing.Iterable`][],
but it may have a different type than was provided. In particular, even if a non-generator type such as a `list`
is provided, the post-validation value of a field of type [`typing.Iterable`][] will be a generator.

Here is a simple example using [`typing.Sequence`][]:

```python
from collections.abc import Sequence

from pydantic import BaseModel


class Model(BaseModel):
    sequence_of_ints: Sequence[int]


print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
#> [1, 2, 3, 4]
print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
#> (1, 2, 3, 4)
```

### Infinite Generators

If you have a generator you want to validate, you can still use `Sequence` as described above.
In that case, the generator will be consumed and stored on the model as a list and its values will be
validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`).

However, if you have a generator that you *don't* want to be eagerly consumed (e.g. an infinite
generator or a remote data loader), you can use a field of type [`Iterable`][typing.Iterable]:

```python
from collections.abc import Iterable

from pydantic import BaseModel


class Model(BaseModel):
    infinite: Iterable[int]


def infinite_ints():
    i = 0
    while True:
        yield i
        i += 1


m = Model(infinite=infinite_ints())
print(m)
"""
infinite=ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))
"""

for i in m.infinite:
    print(i)
    #> 0
    #> 1
    #> 2
    #> 3
    #> 4
    #> 5
    #> 6
    #> 7
    #> 8
    #> 9
    #> 10
    if i == 10:
        break
```

!!! warning
    During initial validation, `Iterable` fields only perform a simple check that the provided argument is iterable.
    To prevent it from being consumed, no validation of the yielded values is performed eagerly.

Though the yielded values are not validated eagerly, they are still validated when yielded, and will raise a
`ValidationError` at yield time when appropriate:

```python
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    int_iterator: Iterable[int]


def my_iterator():
    yield 13
    yield '27'
    yield 'a'


m = Model(int_iterator=my_iterator())
print(next(m.int_iterator))
#> 13
print(next(m.int_iterator))
#> 27
try:
    next(m.int_iterator)
except ValidationError as e:
    print(e)
    """
    1 validation error for ValidatorIterator
    2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    """
```

## Mapping Types

### [`dict`][]

`dict(v)` is used to attempt to convert a dictionary.

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict[str, int]


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x={'foo': '1'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Because of limitations in [typing.TypedDict][] before 3.12, the [typing-extensions](https://pypi.org/project/typing-extensions/)
    package is required for Python <3.12. You'll need to import `TypedDict` from `typing_extensions` instead of `typing` and will
    get a build time error if you don't.

[`TypedDict`][typing.TypedDict] declares a dictionary type that expects all of
its instances to have a certain set of keys, where each key is associated with a value of a consistent type.

It is same as [`dict`][] but Pydantic will validate the dictionary since keys are annotated.

```python
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


ta = TypeAdapter(User)

print(ta.validate_python({'name': 'foo', 'id': 1}))
#> {'name': 'foo', 'id': 1}

try:
    ta.validate_python({'name': 'foo'})
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    id
      Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
    """
```

You can define `__pydantic_config__` to change the model inherited from [`TypedDict`][typing.TypedDict].
See the [`ConfigDict` API reference][pydantic.config.ConfigDict] for more details.

```python
from typing import Optional

from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: Optional[str]
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    identity: UserIdentity
    age: int


ta = TypeAdapter(User)

print(
    ta.validate_python(
        {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(
    ta.validate_python(
        {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': None, 'surname': 'John'}, 'age': 37}

print(ta.validate_python({'identity': {}, 'age': 37}))
#> {'identity': {}, 'age': 37}


try:
    ta.validate_python(
        {'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24}
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    identity.name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    ta.validate_python(
        {
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```

## Callable

See below for more detail on parsing and validation

Fields can also be of type [`Callable`][typing.Callable]:

```python
from typing import Callable

from pydantic import BaseModel


class Foo(BaseModel):
    callback: Callable[[int], int]


m = Foo(callback=lambda x: x)
print(m)
#> callback=<function <lambda> at 0x0123456789ab>
```

!!! warning
    Callable fields only perform a simple check that the argument is
    callable; no validation of arguments, their types, or the return
    type is performed.

## IP Address Types

* [`ipaddress.IPv4Address`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Interface`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
* [`ipaddress.IPv4Network`][]: Uses the type itself for validation by passing the value to `IPv4Network(v)`.
* [`ipaddress.IPv6Address`][]: Uses the type itself for validation by passing the value to `IPv6Address(v)`.
* [`ipaddress.IPv6Interface`][]: Uses the type itself for validation by passing the value to `IPv6Interface(v)`.
* [`ipaddress.IPv6Network`][]: Uses the type itself for validation by passing the value to `IPv6Network(v)`.

See [Network Types](../api/networks.md) for other custom IP address types.

## UUID

For UUID, Pydantic tries to use the type itself for validation by passing the value to `UUID(v)`.
There's a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`.

In case you want to constrain the UUID version, you can check the following types:

* [`UUID1`][pydantic.types.UUID1]: requires UUID version 1.
* [`UUID3`][pydantic.types.UUID3]: requires UUID version 3.
* [`UUID4`][pydantic.types.UUID4]: requires UUID version 4.
* [`UUID5`][pydantic.types.UUID5]: requires UUID version 5.

## Union

Pydantic has extensive support for union validation, both [`typing.Union`][] and Python 3.10's pipe syntax (`A | B`) are supported.
Read more in the [`Unions`](../concepts/unions.md) section of the concepts docs.

## [`type`][]

Pydantic supports the use of `type[T]` to specify that a field may only accept classes (not instances)
that are subclasses of `T`.

```python
from pydantic import BaseModel, ValidationError


class Foo:
    pass


class Bar(Foo):
    pass


class Other:
    pass


class SimpleModel(BaseModel):
    just_subclasses: type[Foo]


SimpleModel(just_subclasses=Foo)
SimpleModel(just_subclasses=Bar)
try:
    SimpleModel(just_subclasses=Other)
except ValidationError as e:
    print(e)
    """
    1 validation error for SimpleModel
    just_subclasses
      Input should be a subclass of Foo [type=is_subclass_of, input_value=<class '__main__.Other'>, input_type=type]
    """
```

You may also use `type` to specify that any class is allowed.

```python {upgrade="skip"}
from pydantic import BaseModel, ValidationError


class Foo:
    pass


class LenientSimpleModel(BaseModel):
    any_class_goes: type


LenientSimpleModel(any_class_goes=int)
LenientSimpleModel(any_class_goes=Foo)
try:
    LenientSimpleModel(any_class_goes=Foo())
except ValidationError as e:
    print(e)
    """
    1 validation error for LenientSimpleModel
    any_class_goes
      Input should be a type [type=is_type, input_value=<__main__.Foo object at 0x0123456789ab>, input_type=Foo]
    """
```

## [`typing.TypeVar`][]

[`TypeVar`][typing.TypeVar] is supported either unconstrained, constrained or with a bound.

```python
from typing import TypeVar

from pydantic import BaseModel

Foobar = TypeVar('Foobar')
BoundFloat = TypeVar('BoundFloat', bound=float)
IntStr = TypeVar('IntStr', int, str)


class Model(BaseModel):
    a: Foobar  # equivalent of ": Any"
    b: BoundFloat  # equivalent of ": float"
    c: IntStr  # equivalent of ": Union[int, str]"


print(Model(a=[1], b=4.2, c='x'))
#> a=[1] b=4.2 c='x'

# a may be None
print(Model(a=None, b=1, c=1))
#> a=None b=1.0 c=1
```

## None Types

[`None`][], `type(None)`, or `Literal[None]` are all equivalent according to [the typing specification](https://typing.readthedocs.io/en/latest/spec/special-types.html#none).
Allows only `None` value.


## Bytes

[`bytes`][] are accepted as-is. [`bytearray`][] is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. See [ByteSize](types.md#pydantic.types.ByteSize) for more details.

## [`typing.Literal`][]

Pydantic supports the use of [`typing.Literal`][] as a lightweight way to specify that a field may accept only specific literal values:

```python
from typing import Literal

from pydantic import BaseModel, ValidationError


class Pie(BaseModel):
    flavor: Literal['apple', 'pumpkin']


Pie(flavor='apple')
Pie(flavor='pumpkin')
try:
    Pie(flavor='cherry')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for Pie
    flavor
      Input should be 'apple' or 'pumpkin' [type=literal_error, input_value='cherry', input_type=str]
    """
```

One benefit of this field type is that it can be used to check for equality with one or more specific values
without needing to declare custom validators:

```python
from typing import ClassVar, Literal, Union

from pydantic import BaseModel, ValidationError


class Cake(BaseModel):
    kind: Literal['cake']
    required_utensils: ClassVar[list[str]] = ['fork', 'knife']


class IceCream(BaseModel):
    kind: Literal['icecream']
    required_utensils: ClassVar[list[str]] = ['spoon']


class Meal(BaseModel):
    dessert: Union[Cake, IceCream]


print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Cake
print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
#> IceCream
try:
    Meal(dessert={'kind': 'pie'})
except ValidationError as e:
    print(str(e))
    """
    2 validation errors for Meal
    dessert.Cake.kind
      Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
    dessert.IceCream.kind
      Input should be 'icecream' [type=literal_error, input_value='pie', input_type=str]
    """
```

With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:

```python
from typing import Literal, Optional, Union

from pydantic import BaseModel


class Dessert(BaseModel):
    kind: str


class Pie(Dessert):
    kind: Literal['pie']
    flavor: Optional[str]


class ApplePie(Pie):
    flavor: Literal['apple']


class PumpkinPie(Pie):
    flavor: Literal['pumpkin']


class Meal(BaseModel):
    dessert: Union[ApplePie, PumpkinPie, Pie, Dessert]


print(type(Meal(dessert={'kind': 'pie', 'flavor': 'apple'}).dessert).__name__)
#> ApplePie
print(type(Meal(dessert={'kind': 'pie', 'flavor': 'pumpkin'}).dessert).__name__)
#> PumpkinPie
print(type(Meal(dessert={'kind': 'pie'}).dessert).__name__)
#> Dessert
print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
#> Dessert
```

## [`typing.Any`][]

Allows any value, including `None`.

## [`typing.Hashable`][]

* From Python, supports any data that passes an `isinstance(v, Hashable)` check.
* From JSON, first loads the data via an `Any` validator, then checks if the data is hashable with `isinstance(v, Hashable)`.

## [`typing.Annotated`][]

Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](../concepts/types.md#using-the-annotated-pattern), but otherwise the additional metadata is ignored and the root type is used.

## [`typing.Pattern`][]

Will cause the input value to be passed to `re.compile(v)` to create a regular expression pattern.

## [`pathlib.Path`][]

Simply uses the type itself for validation by passing the value to `Path(v)`.
