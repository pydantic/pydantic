

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
from pydantic import (
    BaseModel,
    StrictBool,
    StrictBytes,
    StrictInt,
    ValidationError,
    confloat,
)


class StrictBytesModel(BaseModel):
    strict_bytes: StrictBytes


try:
    StrictBytesModel(strict_bytes='hello world')
except ValidationError as e:
    print(e)
    """
    1 validation error for StrictBytesModel
    strict_bytes
      Input should be a valid bytes [type=bytes_type, input_value='hello world', input_type=str]
    """


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


class ConstrainedFloatModel(BaseModel):
    constrained_float: confloat(strict=True, ge=0.0)


try:
    ConstrainedFloatModel(constrained_float=3)
except ValidationError as e:
    print(e)

try:
    ConstrainedFloatModel(constrained_float=-1.23)
except ValidationError as e:
    print(e)
    """
    1 validation error for ConstrainedFloatModel
    constrained_float
      Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1.23, input_type=float]
    """


class StrictBoolModel(BaseModel):
    strict_bool: StrictBool


try:
    StrictBoolModel(strict_bool='False')
except ValidationError as e:
    print(str(e))
    """
    1 validation error for StrictBoolModel
    strict_bool
      Input should be a valid boolean [type=bool_type, input_value='False', input_type=str]
    """
```