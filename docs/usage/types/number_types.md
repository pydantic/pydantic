`int`
: *pydantic* uses `int(v)` to coerce types to an `int`;
  see [this](../models.md#data-conversion) warning on loss of information during data conversion

`float`
: similarly, `float(v)` is used to coerce values to floats

`enum.IntEnum`
: checks that the value is a valid IntEnum instance

`subclass of enum.IntEnum`
: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](#enums-and-choices) for more details

`decimal.Decimal`
: *pydantic* attempts to convert the value to a string, then passes the string to `Decimal(v)`

`NegativeFloat`
: allows a float which is negative; uses standard `float` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`NegativeInt`
: allows an int which is negative; uses standard `int` parsing then checks the value is less than 0;
  see [Constrained Types](#constrained-types)

`PositiveFloat`
: allows a float which is positive; uses standard `float` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`PositiveInt`
: allows an int which is positive; uses standard `int` parsing then checks the value is greater than 0;
  see [Constrained Types](#constrained-types)

`condecimal`
: type method for constraining Decimals;
  see [Constrained Types](#constrained-types)

`confloat`
: type method for constraining floats;
  see [Constrained Types](#constrained-types)

`conint`
: type method for constraining ints;
  see [Constrained Types](#constrained-types)

## Constrained Types

The value of numerous common types can be restricted using `con*` type functions:

```py
from decimal import Decimal

from pydantic import BaseModel, condecimal, confloat, conint


class Model(BaseModel):
    big_int: conint(gt=1000, lt=1024)
    mod_int: conint(multiple_of=5)
    big_float: confloat(gt=1000, lt=1024)
    unit_interval: confloat(ge=0, le=1)
    mod_float: confloat(multiple_of=0.5)
    decimal_positive: condecimal(gt=0)
    decimal_negative: condecimal(lt=0)
    decimal_max_digits_and_places: condecimal(max_digits=2, decimal_places=2)
    mod_decimal: condecimal(multiple_of=Decimal('0.25'))
```

Where `Field` refers to the [field function](../schema.md#field-customisation).

### Arguments to `conint`
The following arguments are available when using the `conint` type function

- `strict: bool = False`: controls type coercion
- `gt: int = None`: enforces integer to be greater than the set value
- `ge: int = None`: enforces integer to be greater than or equal to the set value
- `lt: int = None`: enforces integer to be less than the set value
- `le: int = None`: enforces integer to be less than or equal to the set value
- `multiple_of: int = None`: enforces integer to be a multiple of the set value

### Arguments to `confloat`
The following arguments are available when using the `confloat` type function

- `strict: bool = False`: controls type coercion
- `gt: float = None`: enforces float to be greater than the set value
- `ge: float = None`: enforces float to be greater than or equal to the set value
- `lt: float = None`: enforces float to be less than the set value
- `le: float = None`: enforces float to be less than or equal to the set value
- `multiple_of: float = None`: enforces float to be a multiple of the set value
- `allow_inf_nan: bool = True`: whether to allows infinity (`+inf` an `-inf`) and NaN values, defaults to `True`,
  set to `False` for compatibility with `JSON`,
  see [#3994](https://github.com/pydantic/pydantic/pull/3994) for more details, added in **V1.10**

### Arguments to `condecimal`
The following arguments are available when using the `condecimal` type function

- `gt: Decimal = None`: enforces decimal to be greater than the set value
- `ge: Decimal = None`: enforces decimal to be greater than or equal to the set value
- `lt: Decimal = None`: enforces decimal to be less than the set value
- `le: Decimal = None`: enforces decimal to be less than or equal to the set value
- `max_digits: int = None`: maximum number of digits within the decimal. it does not include a zero before the decimal point or trailing decimal zeroes
- `decimal_places: int = None`: max number of decimal places allowed. it does not include trailing decimal zeroes
- `multiple_of: Decimal = None`: enforces decimal to be a multiple of the set value

## Strict Types

You can use the `StrictStr`, `StrictBytes`, `StrictInt`, `StrictFloat`, and `StrictBool` types
to prevent coercion from compatible types.
These types will only pass validation when the validated value is of the respective type or is a subtype of that type.
This behavior is also exposed via the `strict` field of the `ConstrainedStr`, `ConstrainedBytes`,
`ConstrainedFloat` and `ConstrainedInt` classes and can be combined with a multitude of complex validation rules.

The following caveats apply:

- `StrictBytes` (and the `strict` option of `ConstrainedBytes`) will accept both `bytes`,
   and `bytearray` types.
- `StrictInt` (and the `strict` option of `ConstrainedInt`) will not accept `bool` types,
    even though `bool` is a subclass of `int` in Python. Other subclasses will work.
- `StrictFloat` (and the `strict` option of `ConstrainedFloat`) will not accept `int`.

```py
from pydantic import BaseModel, StrictInt, ValidationError


class StrictIntModel(BaseModel):
    strict_int: StrictInt


try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictIntModel
    strict_int
      Input should be a valid integer [type=int_type, input_value=3.14159, input_type=float]
    """
```
