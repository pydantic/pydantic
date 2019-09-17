from pydantic import BaseModel, confloat,  StrictBool, StrictInt, ValidationError


class StrictIntModel(BaseModel):
    strict_int: StrictInt

try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)
"""
1 validation error for StrictIntModel
strict_int
  value is not a valid integer (type=type_error.integer)
"""

class ConstrainedFloatModel(BaseModel):
    constrained_float: confloat(strict=True, ge=0.0)

try:
    ConstrainedFloatModel(constrained_float=3)
except ValidationError as e:
    print(e)
"""
1 validation error for ConstrainedFloatModel
constrained_float
  value is not a valid float (type=type_error.float)
"""

try:
    ConstrainedFloatModel(constrained_float=-1.23)
except ValidationError as e:
    print(e)
"""
1 validation error for ConstrainedFloatModel
constrained_float
  ensure this value is greater than or equal to 0.0 (type=value_error.number.not_ge; limit_value=0.0)
"""

class StrictBoolModel(BaseModel):
    strict_bool: StrictBool

try:
    StrictBoolModel(strict_bool='False')
except ValidationError as e:
    print(str(e))
"""
1 validation error
strict_bool
  value is not a valid boolean (type=value_error.strictbool)
"""
