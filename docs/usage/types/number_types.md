---
description: Support for number types.
---

Pydantic supports the following numeric types from the Python standard library:

* `int`
* `float`
* `enum.IntEnum`
* `decimal.Decimal`

## Validation of numeric types

`int`
: Pydantic uses `int(v)` to coerce types to an `int`;
  see [Data conversion](../models.md#data-conversion) for details on loss of information during data conversion.

`float`
: similarly, `float(v)` is used to coerce values to floats.

`enum.IntEnum`
: checks that the value is a valid `IntEnum` instance.

subclass of `enum.IntEnum`
: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](enums.md) for more details.

`decimal.Decimal`
: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.

## Constrained types

Pydantic provides functions that can be used to constrain numbers:

* [`conint`][pydantic.types.conint]: Add constraints to an `int` type.
* [`confloat`][pydantic.types.confloat]: Add constraints to a `float` type.
* [`condecimal`][pydantic.types.condecimal]: Add constraints to a `decimal.Decimal` type.

Those functions accept the following arguments:

* `gt` (greater than)
* `ge` (greater than or equal to)
* `lt` (less than)
* `le` (less than or equal to)
* `multiple_of` (multiple of)
* `strict` (whether to allow coercion from compatible types)

Some functions accept additional arguments, which you can see in the API reference of each function. For example,
`confloat` accepts an `allow_inf_nan`, which specifies whether to allow `-inf`, `inf`, and `nan`.

### Constrained integers

There are also types that can be used to constrain integers:

* [`PositiveInt`][pydantic.types.PositiveInt]: Constrain an `int` to be positive.
* [`NegativeInt`][pydantic.types.NegativeInt]: Constrain an `int` to be negative.
* [`NonPositiveInt`][pydantic.types.NonPositiveInt]: Constrain an `int` to be non-positive.
* [`NonNegativeInt`][pydantic.types.NonNegativeInt]: Constrain an `int` to be non-negative.

```py
from pydantic import (
    BaseModel,
    NegativeInt,
    NonNegativeInt,
    NonPositiveInt,
    PositiveInt,
)


class Model(BaseModel):
    positive: PositiveInt
    negative: NegativeInt
    non_positive: NonPositiveInt
    non_negative: NonNegativeInt


m = Model(positive=1, negative=-1, non_positive=0, non_negative=0)
print(m)
#> positive=1 negative=-1 non_positive=0 non_negative=0
```

### Constrained floats

There are also types that can be used to constrain floats:

* [`PositiveFloat`][pydantic.types.PositiveFloat]: Constrain a `float` to be positive.
* [`NegativeFloat`][pydantic.types.NegativeFloat]: Constrain a `float` to be negative.
* [`NonPositiveFloat`][pydantic.types.NonPositiveFloat]: Constrain a `float` to be non-positive.
* [`NonNegativeFloat`][pydantic.types.NonNegativeFloat]: Constrain a `float` to be non-negative.

```py
from pydantic import (
    BaseModel,
    NegativeFloat,
    NonNegativeFloat,
    NonPositiveFloat,
    PositiveFloat,
)


class Model(BaseModel):
    positive: PositiveFloat
    negative: NegativeFloat
    non_positive: NonPositiveFloat
    non_negative: NonNegativeFloat


m = Model(positive=1.0, negative=-1.0, non_positive=0.0, non_negative=0.0)
print(m)
#> positive=1.0 negative=-1.0 non_positive=0.0 non_negative=0.0
```

Besides the above, you can also have a [`FiniteFloat`][pydantic.types.FiniteFloat] type that will only accept finite values (i.e. not `inf`, `-inf` or `nan`).

```py
from pydantic import BaseModel, FiniteFloat


class Model(BaseModel):
    finite: FiniteFloat


m = Model(finite=1.0)
print(m)
#> finite=1.0
```
