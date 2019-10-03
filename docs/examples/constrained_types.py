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


m = Model(
    short_bytes=b'foo',
    strip_bytes=b'   bar',
    short_str='foo',
    regex_str='apple pie',
    strip_str='   bar',
    big_int=1001,
    mod_int=155,
    pos_int=1,
    neg_int=-1,
    big_float=1002.1,
    mod_float=1.5,
    pos_float=2.2,
    neg_float=-2.3,
    unit_interval=0.5,
    short_list=[1, 2],
    decimal_positive='21.12',
    decimal_negative='-21.12',
    decimal_max_digits_and_places='0.99',
    mod_decimal='2.75',
)
debug(m.dict())
"""
{
    'short_bytes': b'foo',
    'strip_bytes': b'bar',
    'short_str': 'foo',
    'regex_str': 'apple pie',
    'strip_str': 'bar',
    'big_int': 1001,
    'mod_int': 155,
    'pos_int': 1,
    'neg_int': -1,
    'big_float': 1002.1,
    'unit_interval': 0.5,
    'mod_float': 1.5,
    'pos_float': 2.2,
    'neg_float': -2.3,
    'short_list': [1, 2],
    'decimal_positive': Decimal('21.12'),
    'decimal_negative': Decimal('-21.12'),
    'decimal_max_digits_and_places': Decimal('0.99'),
    'mod_decimal': Decimal('2.75'),
}
"""
