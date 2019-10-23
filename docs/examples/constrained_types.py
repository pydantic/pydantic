from decimal import Decimal

from pydantic import (
    BaseModel,
    NegativeFloat,
    NegativeInt,
    PositiveFloat,
    PositiveInt,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    constr,
    Field,
)

class Model(BaseModel):
    short_bytes: conbytes(min_length=2, max_length=10)
    strip_bytes: conbytes(strip_whitespace=True)

    short_str: constr(min_length=2, max_length=10)
    regex_str: constr(regex='apple (pie|tart|sandwich)')
    strip_str: constr(strip_whitespace=True)

    big_int: conint(gt=1000, lt=1024)
    mod_int: conint(multiple_of=5)
    pos_int: PositiveInt
    neg_int: NegativeInt

    big_float: confloat(gt=1000, lt=1024)
    unit_interval: confloat(ge=0, le=1)
    mod_float: confloat(multiple_of=0.5)
    pos_float: PositiveFloat
    neg_float: NegativeFloat

    short_list: conlist(int, min_items=1, max_items=4)

    decimal_positive: condecimal(gt=0)
    decimal_negative: condecimal(lt=0)
    decimal_max_digits_and_places: condecimal(max_digits=2, decimal_places=2)
    mod_decimal: condecimal(multiple_of=Decimal('0.25'))

    bigger_int: int = Field(..., gt=10000)
