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
  see [this](../models.md#data-conversion) warning on loss of information during data conversion

`float`
: similarly, `float(v)` is used to coerce values to floats

`enum.IntEnum`
: checks that the value is a valid IntEnum instance

`subclass of enum.IntEnum`
: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enums-and-choices) for more details

`decimal.Decimal`
: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`

## Constrained Types

Pydantic provides functions that can be used to constrain numbers:

* `conint`: Add constraints to an `int` type.
* `confloat`: Add constraints to a `float` type.
* `condecimal`: Add constraints to a `decimal.Decimal` type.

Those functions accept the following arguments:

* `gt` (greater than)
* `ge` (greater than or equal to)
* `lt` (less than)
* `le` (less than or equal to)
* `multiple_of` (multiple of)
* `strict` (whether to allow coercion from compatible types)

There are other arguments for each function, which you can see in the API Reference of each function:

  * [`conint`](/api/types/#conint)
  * [`confloat`](/api/types/#confloat)
  * [`condecimal`](/api/types/#condecimal)

### Constrained Integers

There are also types that can be used to constrain integers:

* [`PositiveInt`]: Constrain an `int` to be positive.
* [`NegativeInt`]: Constrain an `int` to be negative.
* [`NonPositiveInt`]: Constrain an `int` to be non-positive.
* [`NonNegativeInt`]: Constrain an `int` to be non-negative.

```py
from pydantic import BaseModel, NegativeInt, NonNegativeInt, NonPositiveInt, PositiveInt


class Model(BaseModel):
    positive: PositiveInt
    negative: NegativeInt
    non_positive: NonPositiveInt
    non_negative: NonNegativeInt


m = Model(positive=1, negative=-1, non_positive=0, non_negative=0)
print(m)
#> positive=1 negative=-1 non_positive=0 non_negative=0
```

### Constrained Floats

There are also types that can be used to constrain floats:

* [`PositiveFloat`]: Constrain a `float` to be positive.
* [`NegativeFloat`]: Constrain a `float` to be negative.
* [`NonPositiveFloat`]: Constrain a `float` to be non-positive.
* [`NonNegativeFloat`]: Constrain a `float` to be non-negative.

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

Besides the above, you can also have a `FiniteFloat` type that will only accept finite values (i.e. not `inf`, `-inf` or `nan`).

```py
from pydantic import BaseModel, FiniteFloat


class Model(BaseModel):
    finite: FiniteFloat


m = Model(finite=1.0)
print(m)
#> finite=1.0
```

[`PositiveInt`]: /api/types/#pydantic.types.PositiveInt
[`NegativeInt`]: /api/types/#pydantic.types.NegativeInt
[`NonPositiveInt`]: /api/types/#pydantic.types.NonPositiveInt
[`NonNegativeInt`]: /api/types/#pydantic.types.NonNegativeInt
[`PositiveFloat`]: /api/types/#pydantic.types.PositiveFloat
[`NegativeFloat`]: /api/types/#pydantic.types.NegativeFloat
[`NonPositiveFloat`]: /api/types/#pydantic.types.NonPositiveFloat
[`NonNegativeFloat`]: /api/types/#pydantic.types.NonNegativeFloat
[`StrictBytes`]: /api/types/#pydantic.types.StrictBytes
[`StrictInt`]: /api/types/#pydantic.types.StrictInt
[`StrictFloat`]: /api/types/#pydantic.types.StrictFloat
