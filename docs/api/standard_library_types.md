---
description: Support for common types from the Python standard library.
---

This section enumerates the supported built-in and standard library types: the allowed values,
the possible constraints, and whether strictness can be configured.

See also the [conversion table](../concepts/conversion_table.md) for a summary of the allowed values for each type.

!!! note
    Unless specified otherwise, values are serialized as-is, in both Python and JSON modes.

## Booleans

Built-in type: [`bool`][]

<h3>Validation</h3>

* A valid [`bool`][] instance, i.e. `True` or `False`.
* The integers `0` or `1`.
* A string, which when converted to lowercase is one of `'0'`, `'off'`, `'f'`, `'false'`, `'n'`, `'no'`, `'1'`, `'on'` `'t'`, `'true'`, `'y'`, `'yes'`.
* [`bytes`][] objects that are valid per the previous rule when decoded to a string.

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

* Strings are accepted as-is.
* [`bytes`][] and [`bytearray`][] are decoded to UTF-8 strings.
* [Enums][enum] are converted using the [`value`][enum.Enum.value] attribute, by calling [`str()`][str]
  on it.
* If [`coerce_numbers_to_str`][pydantic.ConfigDict.coerce_numbers_to_str] is set, any number type
  ([`int`][], [`float`][] and [`Decimal`][decimal.Decimal]) will be coerced to a string and accepted
  as-is.

<h3>Constraints</h3>

Strings support the following constraints:

| Constraint         | Description                                       | JSON Schema                                                                                                                                   |
| ------------------ | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `pattern`          | A regex pattern that the string must match        | [`pattern`](https://json-schema.org/understanding-json-schema/reference/string#regexp) keyword (see [note](#pattern-constraint-note) below).  |
| `min_length`       | The minimum length of the string                  | [`minLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword                                              |
| `max_length`       | The maximum length of the string                  | [`maxLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword                                              |
| `strip_whitespace` | Whether to remove leading and trailing whitespace | N/A                                                                                                                                           |
| `to_upper`         | Whether to convert the string to uppercase        | N/A                                                                                                                                           |
| `to_lower`         | Whether to convert the string to lowercase        | N/A                                                                                                                                           |

These constraints can be provided using the [`StringConstraints`][pydantic.types.StringConstraints] metadata type, or using the [`Field()`][pydantic.Field] function (except for `to_upper` and `to_lower`).

The [`annotated-types`](https://github.com/annotated-types/annotated-types) library also provides the `MinLen`, `MaxLen` and `Len` metadata types, as well
as the `LowerCase`, `UpperCase`, `IsDigit` and `IsAscii` predicates (must be parameterized with `str`, e.g. `LowerCase[str]`).

<!-- markdownlint-disable-next-line no-empty-links -->
[](){#pattern-constraint-note}

!!! note "`pattern` constraint"
    By default, Pydantic will use the [`regex`](https://docs.rs/regex) Rust crate to enforce the `pattern` constraint. The regex engine can be controlled
    using the [`regex_engine`][pydantic.ConfigDict.regex_engine] configuration value. If a compiled [regular expression object][re.Pattern] is used for
    `pattern`, the Python engine will automatically be used.

    While the JSON Schema specification [recommends](https://json-schema.org/draft/2020-12/json-schema-core#name-regular-expressions) using patterns
    valid according to dialect described in [ECMA-262](https://262.ecma-international.org/11.0/index.html#sec-patterns), Pydantic will *not* enforce it.

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only string values are valid. Pydantic provides the [`StrictStr`][pydantic.types.StrictStr]
type as a convenience to [using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<h3>Example</h3>

```python
from typing import Annotated

from pydantic import BaseModel, StringConstraints


class StringModel(BaseModel):
    str_value: str = ""
    constrained_str_value: Annotated[str, StringConstraints(to_lower=True)] = ""


print(StringModel(str_value="test").str_value)
#> test
print(StringModel(constrained_str_value='TEST').constrained_str_value)
#> test
```

## Bytes

Built-in type: [`bytes`][].

See also: [`ByteSize`][pydantic.types.ByteSize].

<h3>Validation</h3>

* [`bytes`][] instances are validated as is.
* Strings and [`bytearray`][] instances are converted as bytes, following the [`val_json_bytes`][pydantic.ConfigDict.val_json_bytes] configuration value
  (despite its name, it applies to both Python and JSON modes).

<h3>Constraints</h3>

Strings support the following constraints:

| Constraint         | Description                     | JSON Schema                                                                                      |
| ------------------ | --------------------------------| -------------------------------------------------------------------------------------------------|
| `min_length`       | The minimum length of the bytes | [`minLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword |
| `max_length`       | The maximum length of the bytes | [`maxLength`](https://json-schema.org/understanding-json-schema/reference/string#length) keyword |

The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only [`bytes`][] instances are valid. Pydantic provides the [`StrictBytes`][pydantic.types.StrictBytes]
type as a convenience to [using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

In JSON mode, strict mode has no effect.

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

* Integers are validated as-is.
* Strings and bytes are attempted to be converted to integers and validated as-is
  (see the [jiter implementation](https://docs.rs/jiter/latest/jiter/enum.NumberInt.html#impl-TryFrom%3C%26%5Bu8%5D%3E-for-NumberInt) for details).
* Floats are validated as integers, provided the float input is not infinite or a NaN (not-a-number)
  and the fractional part is 0.
* [`Decimal`][decimal.Decimal] instances, provided they are [finite][decimal.Decimal.is_finite] and the
  denominator is 1.
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

* Floats are validated as-is.
* String and bytes are attempted to be converted to floats and validated as-is.
  (see the [Rust implementation](https://doc.rust-lang.org/src/core/num/dec2flt/mod.rs.html) for details).
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

The [`annotated-types`](https://github.com/annotated-types/annotated-types) library also provides the `Le`, `Ge`, `Lt`, `Gt` and `MultipleOf` metadata types,
as well as the `IsFinite`, `IsNotFinite`, `IsNan`, `IsNotNan`, `IsAscii`, `IsInfinite` and `IsNotInfinite` predicates
(must be parameterized with `float`, e.g. `IsFinite[float]`). The [`AllowInfNan`][pydantic.types.AllowInfNan] type can also be used.

Pydantic also provides the following types as convenience aliases:

* [`PositiveFloat`][pydantic.types.PositiveFloat]: Requires the input to be greater than zero.
* [`NegativeFloat`][pydantic.types.NegativeFloat]: Requires the input to be less than zero.
* [`NonPositiveFloat`][pydantic.types.NonPositiveFloat]: Requires the input to be less than or equal to zero.
* [`NonNegativeFloat`][pydantic.types.NonNegativeFloat]: Requires the input to be greater than or equal to zero.
* [`FiniteFloat`][pydantic.types.FiniteFloat]: Prevents NaN (not-a-number) and infinite values.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only float values and inputs having a [`__float__()`][object.__float__]
or [`__index__()`][object.__index__] method are valid.
Pydantic provides the [`StrictFloat`][pydantic.types.StrictFloat] type as a convenience to
[using the `Strict()` metadata class](../concepts/strict_mode.md#using-the-strict-metadata-class).

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#enumintenum}

### Integer enums

Standard library type: [`enum.IntEnum`][].

<h4>Validation</h4>

* If the [`enum.IntEnum`][] type is used directly, any [`enum.IntEnum`][] instance is validated as-is
* If an [`enum.IntEnum`][] subclass is used as a type, any enum member or value that correspond to the
  enum members values is validated as-is.

See [Enums](#enums) for more details.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#decimaldecimal}

### Decimals

Standard library type: [`decimal.Decimal`][].

<h4>Validation</h4>

* [`Decimal`][decimal.Decimal] instances are validated as is.
* Any value accepted by the [`Decimal`][decimal.Decimal] constructor.

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
#> {"f":2.1}
```

1. In Python mode, `f`remains a [`Decimal`][decimal.Decimal] instance.
2. In JSON mode, `f` is serialized as a float.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#complex}

### Complex numbers

Built-in type: [`complex`][].

<h4>Validation</h4>

* [`complex`][] instances are validated as-is.
* In Python mode, data is validated using the [`complex()`][complex] constructor.
* In JSON mode, string are validated using the [`complex()`][complex] constructor,
   numbers (integers and floats) are used as the real part.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`complex`][] instances are accepted. In JSON mode, only strings that are
accepted by the [`complex()`][complex] constructor are allowed.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`complex`][] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#fractionsfraction}

### Fractions

Standard library type: [`fractions.Fraction`][].

<h4>Validation</h4>

* [`Fraction`][fractions.Fraction] instances are validated as is.
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
[](){#datetimedatetime}

### Datetimes

Standard library type: [`datetime.datetime`][].

<h4>Validation</h4>

* [`datetime`][datetime.datetime] instances are validated as is.
* Strings and bytes are validated in two ways:
    * Strings complying to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format (both datetime and date).
      See the [speedate](https://docs.rs/speedate/) documentation for more details.
    * Unix timestamps, both as seconds or milliseconds sinch the [epoch](https://en.wikipedia.org/wiki/Unix_time).
      See the [`val_temporal_unit`][pydantic.ConfigDict.val_temporal_unit] configuration value for more details.
* Integers and floats (or types that can be coerced as integers or floats) are validated as unix timestamps, following the
  same semantics as strings.
* [`datetime.date`][] instances are accepted, and converted to a [`datetime`][datetime.datetime] instance
  by setting the [`hour`][datetime.datetime.hour], [`minute`][datetime.datetime.minute], [`second`][datetime.datetime.second] and
  [`microsecond`][datetime.datetime.microsecond] attributes to `0`, and the [`tzinfo`][datetime.datetime.tzinfo] attribute to `None`.

!!! note
    Named timezone support (as specified in [RFC 9557](https://datatracker.ietf.org/doc/html/rfc9557.html))
    can be tracked in [this issue](https://github.com/pydantic/pydantic/issues/12252).

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`datetime`][datetime.datetime] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

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
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field


class Event(BaseModel):
    dt: Annotated[AwareDatetime, Field(gt=datetime(2000, 1, 1))]


event = Event(dt='2032-04-23T10:20:30.400+02:30')

print(event.model_dump())
"""
{'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(9000))}
"""
print(event.model_dump_json())
#> {"dt":"2032-04-23T10:20:30.400000+02:30"}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetimedate}

### Dates

Standard library type: [`datetime.date`][].

<h4>Validation</h4>

* [`date`][datetime.date] instances are validated as is.
* Strings and bytes are validated in two ways:
    * Strings complying to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) date format.
      See the [speedate](https://docs.rs/speedate/) documentation for more details.
    * Unix timestamps, both as seconds or milliseconds sinch the [epoch](https://en.wikipedia.org/wiki/Unix_time).
      See the [`val_temporal_unit`][pydantic.ConfigDict.val_temporal_unit] configuration value for more details.
* If the validation fails, the input can be [validated as a datetime](#datetimes) (including as numbers),
  provided that the time component is 0 and that it is naive.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`date`][datetime.date] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

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
print(my_birthday.model_dump_json())
#> {"d":"2023-03-24"}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetimetime}

### Time

Standard library type: [`datetime.time`][].

<h4>Validation</h4>

* [`time`][datetime.time] instances are validated as is.
* Strings and bytes are validated according to the [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) time format.
* Integers and floats (or values that can be coerced to such numbers) are validated as seconds. The value should not exceed 86 399.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`time`][datetime.time] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

!!! note
    Named timezones from the [IANA time zone database](https://www.iana.org/time-zones) (see the [`zoneinfo`][] module) are *not* serialized
    with time objects. This is consistent with the [`time.isoformat()`][datetime.time.isoformat] method.

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
print(m.model_dump_json())
#> {"t":"04:08:16"}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#datetimetimedelta}

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

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), [`timedelta`][datetime.timedelta] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

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
print(m.model_dump_json())
#> {"td":"P3DT12H30M5S"}
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#enum}

## Enums

Standard library type: [`enum.Enum`][].

<h3>Validation</h3>

* If the [`enum.Enum`][] type is used directly, any [`enum.Enum`][] instance is validated as-is.
* If an [`enum.Enum`][] subclass is used as a type, any enum member or value that correspond to the
  enum members [values][enum.Enum.value] is validated as-is.

<h3>Serialization</h3>

In [Python mode](../concepts/serialization.md#python-mode), enum instances are serialized as is.
The [`use_enum_values`][pydantic.ConfigDict.use_enum_values] configuration value can be set to
use the enum [value][enum.Enum.value] during validation (so that it is also used during serialization).

In [JSON mode](../concepts/serialization.md#json-mode), enum instances are serialized using
their [value][enum.Enum.value].

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

## None types

Supported types: [`None`][], [`NoneType`][types.NoneType] or `Literal[None]` (they are [equivalent](https://typing.readthedocs.io/en/latest/spec/special-types.html#none)).

Allows only `None` as a value.

## Generic collection types

Pydantic supports a wide variety of generic collection types, both built-ins (such as [`list`][]) and abstract base classes
from the [`collections.abc`][] module (such as [`Sequence`][collections.abc.Sequence]).

In most cases, it is recommended to make use of the built-in types over the abstract ones. Due to [data coercion](../concepts/models.md#data-conversion),
using [`list`][] or [`tuple`][] will allow most other iterables as input, with better performance.

!!! note "Strictness on collection types"
    When applying [strict mode](../concepts/strict_mode.md) on collection types, strictness will *not* apply
    to the inner types. This may change in the future, see [this issue](https://github.com/pydantic/pydantic/issues/12319).

### Lists

Built-in type: [`list`][] (deprecated alias: [`typing.List`][]).

<h4>Validation</h4>

* Allows [`list`][], [`tuple`][], [`set`][] and [`frozenset`][] instances, or any iterable that is *not* a
  [string][str], [bytes][], [bytearray][], [dict][] or [mapping][]. Produces a [`list`][] instance.
* If a generic parameter is provided, the appropriate validation is applied to all items of the list.

<h4>Constraints</h4>

Lists support the following constraints:

| Constraint   | Description                                 | JSON Schema                                                                                    |
|--------------|---------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The list must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The list must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`list`][] instances are valid. Strict mode does *not* apply to the items of the list.
The strict constraint must be applied to the parameter type for this to work.

<h4>Example</h4>

```python
from typing import Optional

from pydantic import BaseModel, Field


class Model(BaseModel):
    simple_list: Optional[list[object]] = None
    list_of_ints: Optional[list[int]] = Field(default=None, strict=True)


print(Model(simple_list=('1', '2', '3')).simple_list)
#> ['1', '2', '3']
print(Model(list_of_ints=['1', 2, 3]).list_of_ints)
#> [1, 2, 3]
```

### Tuples

Built-in type: [`tuple`][] (deprecated alias: [`typing.Tuple`][]).

!!! note
    [Unpacked tuple types](https://typing.python.org/en/latest/spec/generics.html#unpacking-tuple-types)
    (as specified by [PEP 646](https://peps.python.org/pep-0646/)) are *not* yet supported, and can be
    tracked in [this issue](https://github.com/pydantic/pydantic/issues/5952).

<h4>Validation</h4>

* Allows [`tuple`][], [`list`][], [`set`][] and [`frozenset`][] instances, or any iterable that is *not* a
  [string][str], [bytes][], [bytearray][], [dict][] or [mapping][]. Produces a [`tuple`][] instance.
* Appropriate validation is applied to items of the tuple, if [element types](https://typing.python.org/en/latest/spec/tuples.html#tuple-type-form)
  are specified.

<h4>Constraints</h4>

Lists support the following constraints:

| Constraint   | Description                                  | JSON Schema                                                                                    |
|--------------|----------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The tuple must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The tuple must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

Additionally, the [`prefixItems`](https://json-schema.org/understanding-json-schema/reference/array#tupleValidation) JSON Schema keyword may be used
depending on the tuple shape.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`tuple`][] instances are valid. Strict mode does *not* apply to the items of the tuple.
The strict constraint must be applied to the parameter types for this to work.

<h4>Example</h4>

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

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingnamedtuple}

### Named tuples

Standard library type: [`typing.NamedTuple`][] (and types created by the [`collections.namedtuple()`][collections.namedtuple] factory function
– each field will implicitly have the type [`Any`][typing.Any]).

<h4>Validation</h4>

* Allows [`tuple`][] and [`list`][] instances. Validate each item according to the field definition.
* Allows [`dict`][] instances. Keys must match the named tuple field names, and values are validated according to the field definition.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), named tuples are serialized as tuples. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as arrays.

<h4>Example</h4>

```python
from typing import NamedTuple

from pydantic import BaseModel


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


model = Model(p=('1', 2))

print(model.model_dump())
#> {'p': (1, 2)}
```

### Sets

Types: [`set`][] (or [`collections.abc.MutableSet`][]) and [`frozenset`][] (or [`collections.abc.Set`][])
(deprecated aliases: [`typing.Set`][] and [`typing.FrozenSet`][]).

<h4>Validation</h4>

* Allows [`set`][], [`frozenset`][], [`tuple`][] and [`list`][] instances, or any iterable that is *not* a
  [string][str], [bytes][], [bytearray][], [dict][] or [mapping][]. Produces a [`set`][] or [`frozenset`][] instance.
* If a generic parameter is provided, the appropriate validation is applied to all items of the set/frozenset.

<h4>Constraints</h4>

Sets support the following constraints:

| Constraint   | Description                                | JSON Schema                                                                                    |
|--------------|--------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The set must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The set must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`set`][]/[`frozenset`][] instances are valid. Strict mode does *not* apply to the items of the set.
The strict constraint must be applied to the parameter type for this to work.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), sets are serialized as is. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as arrays.

<h4>Example</h4>

```python
from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    simple_set: Optional[set] = None
    set_of_ints: Optional[frozenset[int]] = None


print(Model(simple_set=['1', '2', '3']).simple_set)
#> {'1', '2', '3'}
print(Model(set_of_ints=['1', '2', '3']).set_of_ints)
#> frozenset({1, 2, 3})
```

### Deque

Standard library type: [`collections.deque`][] (deprecated alias: [`typing.Deque`][]).

<h4>Validation</h4>

Values are first validated as a [list](#lists), and then passed to the [`deque`][collections.deque] constructor.

<h4>Constraints</h4>

Deques support the following constraints:

| Constraint   | Description                                  | JSON Schema                                                                                    |
|--------------|----------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The deque must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The deque must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`deque`][collections.deque] instances are valid. Strict mode does *not* apply to the items of the deque.
The strict constraint must be applied to the parameter type for this to work.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), deques are serialized as is. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as arrays.

<h4>Example</h4>

```python
from collections import deque

from pydantic import BaseModel


class Model(BaseModel):
    deque: deque[int]


print(Model(deque=[1, 2, 3]).deque)
#> deque([1, 2, 3])
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingsequence}

### Sequences

Standard library type: [`collections.abc.Sequence`][] (deprecated alias: [`typing.Sequence`][]).

In most cases, you will want to use the built-in types (such as [list](#lists) or [tuple](#tuples)) as [type coercion](../concepts/models.md#data-conversion)
will apply. The [`Sequence`][collections.abc.Sequence] type can be used when you want to preserve the input type during serialization.

<h4>Validation</h4>

Any [`collections.abc.Sequence`][] instance (expect strings and bytes) is accepted. It is converted to a list using the [`list()`][list]
constructor, and then converted back to the original input type.

!!! warning "Strings aren't treated as sequences"
    While strings are technically valid sequence instances, this is frequently not intended as is a common source of bugs.

    As a result, Pydantic will *not* accept strings and bytes for the [`Sequence`][collections.abc.Sequence] type (see example below).

<h4>Constraints</h4>

Sequences support the following constraints:

| Constraint   | Description                                     | JSON Schema                                                                                    |
|--------------|-------------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The sequence must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The sequence must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Serialization</h4>

In [Python mode](../concepts/serialization.md#python-mode), sequences are serialized as is. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as arrays.

<h4>Example</h4>

```python
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    sequence_of_strs: Sequence[str]


print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
#> ['a', 'bc']
print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
#> ('a', 'bc')

try:
    Model(sequence_of_strs='abc')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    sequence_of_strs
      'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
    """
```

### Dictionaries

Built-in type: [`dict`][].

<h4>Validation</h4>

* [`dict`][] instances are accepted as is.
* [mappings][mapping] instances are accepted and coerced to a [`dict`][].
* If generic parameters for keys and values are provided, the appropriate validation is applied.

<h4>Constraints</h4>

Dictionaries support the following constraints:

| Constraint   | Description                                       | JSON Schema                                                                                    |
|--------------|---------------------------------------------------|------------------------------------------------------------------------------------------------|
| `min_length` | The dictionary must have at least this many items | [`minItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |
| `max_length` | The dictionary must have at most this many items  | [`maxItems`](https://json-schema.org/understanding-json-schema/reference/array#length) keyword |

These constraints can be provided using the [`Field()`][pydantic.Field] function.
The `MinLen` and `MaxLen` metadata types from the [`annotated-types`](https://github.com/annotated-types/annotated-types)
library can also be used.

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`dict`][] instances are valid. Strict mode does *not* apply to the keys and values of the dictionaries.
The strict constraint must be applied to the parameter types for this to work.

<h4>Example</h4>

```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict[str, int]


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x='test')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typeddict}

### Typed dictionaries

Standard library type: [`typing.TypedDict`][] (see also: the [typing specification](https://typing.python.org/en/latest/spec/typeddict.html)).

!!! note
    Because of runtime limitations, Pydantic will require using the [`TypedDict`][typing_extensions.TypedDict] type from
    [`typing_extensions`][] when using Python 3.12 and lower.

[`TypedDict`][typing.TypedDict] declares a dictionary type that expects all of its instances to have a certain set of keys
 where each key is associated with a value of a consistent type.

This type [supports configuration](../concepts/config.md#configuration-on-other-supported-types).

<h4>Strictness</h4>

In [strict mode](../concepts/strict_mode.md), only [`dict`][] instances are valid (unlike mappings in lax mode).
Strict mode does *not* apply to the values of the typed dictionary. The strict constraint must be applied to the value types for this to work.

<h4>Example</h4>

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

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingiterable}

### Iterables

Standard library type: [`collections.abc.Iterable`][] (deprecated alias: [`typing.Iterable`][]).

<h4>Validation</h4>

Iterables are lazily validated, and wrapped in an internal datastructure that can be iterated over
(and will validate the items type while doing so). This means that even if you provide a concrete
container such as a list, the validated type will *not* be of type [`list`][]. However, Pydantic
will ensure that the input value is iterable by getting an [iterator][] from it (by calling
[`iter()`][iter] on the value).

It is recommended to use concrete collection types (such as [lists](#lists)) instead, unless
you are using an infinite iterator (in which case eagerly validating the input would result
in an infinite loop).

<h4>Example</h4>

```python
from collections.abc import Iterable

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    f: Iterable[str]


m = Model(f=[1, 2])  # Validates fine

try:
    next(m.f)
except ValidationError as e:
    print(e)
    """
    1 validation error for ValidatorIterator
    0
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    """
```

## Callable

Standard library type: [`collections.abc.Callable`][] (deprecated alias: [`typing.Callable`][]).

<h3>Validation</h3>

Pydantic only validates that the input is a [callable][] (using the [`callable()`](https://docs.python.org/3/library/functions.html#callable) function).
It does *not* validate the number of parameters or their type, nor the type of the return value.

```python
from typing import Callable

from pydantic import BaseModel


class Foo(BaseModel):
    callback: Callable[[int], int]


m = Foo(callback=lambda x: x)
print(m)
#> callback=<function <lambda> at 0x0123456789ab>
```

<h3>Serialization</h3>

Callables are serialized as is. Callables can't be serialized in [JSON mode](../concepts/serialization.md#json-mode)
(a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] is raised).

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#ip-address-types}

## IP Addresses

Standard library types:

* [`ipaddress.IPv4Address`][]
* [`ipaddress.IPv4Interface`][]
* [`ipaddress.IPv4Network`][]
* [`ipaddress.IPv6Address`][]
* [`ipaddress.IPv6Interface`][]
* [`ipaddress.IPv6Network`][]

See also: the [`IPvAnyAddress`][pydantic.networks.IPvAnyAddress], [`IPvAnyInterface`][pydantic.networks.IPvAnyInterface]
and [`IPvAnyNetwork`][pydantic.networks.IPvAnyNetwork] Pydantic types.

<h3>Validation</h3>

* Instances are validated as is.
* Other input values are passed to the constructor of the relevant address type.

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only the address types are accepted.
In JSON mode, strict mode has no effect.

<h3>Serialization</h3>

In [Python mode](../concepts/serialization.md#python-mode), IP addresses are serialized as is. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as strings.

## UUID

Standard library type: [`uuid.UUID`][].

<h3>Validation</h3>

* [`UUID`][uuid.UUID] instances are validated as is.
* Strings and bytes are validated as UUIDs, and casted to a [`UUID`][uuid.UUID] instance.

<h3>Constraints</h3>

The [`UUID`][uuid.UUID] type supports a `version` constraint. The [`UuidVersion`][pydantic.types.UuidVersion] metadata type can be used.

Pydantic also provides the following types as convenience aliases: [`UUID1`][pydantic.types.UUID1], [`UUID3`][pydantic.types.UUID3],
[`UUID4`][pydantic.types.UUID4], [`UUID5`][pydantic.types.UUID5], [`UUID6`][pydantic.types.UUID6], [`UUID7`][pydantic.types.UUID7],
[`UUID8`][pydantic.types.UUID8].

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only [`UUID`][uuid.UUID] instances are accepted.
In JSON mode, strict mode has no effect.

<h3>Serialization</h3>

In [Python mode](../concepts/serialization.md#python-mode), UUIDs are serialized as is. In [JSON mode](../concepts/serialization.md#json-mode),
they are serialized as strings.

<h3>Example</h3>

```python
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import UUID7, UuidVersion


class Model(BaseModel):
    u1: UUID7
    u2: Annotated[UUID, UuidVersion(4)]


print(
    Model(
        u1='01999b2c-8353-749b-8dac-859307fae22b',
        u2=UUID('125725f3-e1b4-44e3-90c3-1a20eab12da5'),
    )
)
"""
u1=UUID('01999b2c-8353-749b-8dac-859307fae22b') u2=UUID('125725f3-e1b4-44e3-90c3-1a20eab12da5')
"""
```

## Type

Built-in type: [`type`][] (deprecated alias: [`typing.Type`][]).

<h3>Validation</h3>

Allows any type that is a subclass of the type argument. For instance, with `type[str]`, allows the [`str`][]
class or any [`str`][] subclass as an input. If no type argument is provided (i.e. `type` is used as an annotation),
allow any class.

<h3>Serialization</h3>

Types are serialized as is. Types can't be serialized in [JSON mode](../concepts/serialization.md#json-mode)
(a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] is raised).

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

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingliteral}

## Literals

Typing construct: [`typing.Literal`][] (see also: the [typing specification](https://typing.python.org/en/latest/spec/literal.html#literal)).

Literals can be used to only allow specific literal values.

Note that Pydantic applies [strict mode](../concepts/strict_mode.md) behavior when validating literal values (see [this issue](https://github.com/pydantic/pydantic/issues/9991)).

<h3>Example</h3>

```python
from typing import Literal

from pydantic import BaseModel, ValidationError


class Pie(BaseModel):
    flavor: Literal['apple', 'pumpkin']
    quantity: Literal[1, 2] = 1


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

try:
    Pie(flavor='apple', quantity='1')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for Pie
    quantity
      Input should be 1 or 2 [type=literal_error, input_value='1', input_type=str]
    """
```

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingany}

## Any

Types: [`typing.Any`][] or [`object`][].

Allows any value, including `None`.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typinghashable}

## Hashables

Standard library type: [`collections.abc.Hashable`][] (deprecated alias: [`typing.Hashable`][]).

<h3>Validation</h3>

Any value that is hashable (using `isinstance(value, Hashable)`).

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#typingpattern}

## Regex patterns

Standard library type: [`re.Pattern`][] (deprecated alias: [`typing.Pattern`][]).

<h3>Validation</h3>

* For [`Pattern`][re.Pattern] instances, check that the [`pattern`][re.Pattern.pattern] attribute
  is of the right type ([`str`][] or [`bytes`][] depending on the [`Pattern`][re.Pattern] type
  parameter).
* If the type parameter is [`str`][] or [`bytes`][], input values of type [`str`][] (or [`bytes`][] respectively)
  are attempted to be compiled using [`re.compile()`][re.compile].

<h3>Serialization</h3>

In [Python mode](../concepts/serialization.md#python-mode), [`Pattern`][re.Pattern] instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#pathlibpath}

## Paths

Standard library types:

* [`pathlib.Path`][].
* [`pathlib.PurePath`][].
* [`pathlib.PosixPath`][].
* [`pathlib.PurePosixPath`][].
* [`pathlib.PureWindowsPath`][].
* [`os.PathLike`][] (must be parameterized with [`str`][], [`bytes`][] or [`Any`][typing.Any]).

<h3>Validation</h3>

* Path instances are validated as is.
* Strings are accepted and passed to the type constructor. If [`os.PathLike`][] was used,
  bytes are accepted if it was parameterized with the [`bytes`][] type.

<h3>Strictness</h3>

In [strict mode](../concepts/strict_mode.md), only Path instances are accepted.
In JSON mode, strict mode has no effect.

<h3>Serialization</h3>

In [Python mode](../concepts/serialization.md#python-mode), Path instances are
serialized as is.

In [JSON mode](../concepts/serialization.md#json-mode), they are serialized as strings.
