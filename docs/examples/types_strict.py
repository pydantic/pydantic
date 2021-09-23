from pydantic import (
    BaseModel,
    StrictBytes,
    StrictBool,
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


class StrictIntModel(BaseModel):
    strict_int: StrictInt


try:
    StrictIntModel(strict_int=3.14159)
except ValidationError as e:
    print(e)


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


class StrictBoolModel(BaseModel):
    strict_bool: StrictBool


try:
    StrictBoolModel(strict_bool='False')
except ValidationError as e:
    print(str(e))
