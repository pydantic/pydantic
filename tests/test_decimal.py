"""
Self contained example showcasing problem with decimals using pydantics
default encoder.
"""
from decimal import Decimal

from pydantic import BaseModel, ConstrainedDecimal


class Id(ConstrainedDecimal):
    max_digits = 22
    decimal_places = 0
    ge = 0


ObjId = Id


class Obj(BaseModel):
    id: ObjId
    name: str
    price: Decimal = Decimal('0.01')


def test_con_decimal_encode() -> None:
    test_obj = Obj(id=1, name='Test Obj')
    cycled_obj = Obj.parse_raw(test_obj.json())
    assert test_obj == cycled_obj
