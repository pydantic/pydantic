import calendar
from datetime import date

from pydantic import BaseModel
from pydantic.types import PaymentCardBrand, PaymentCardNumber

class Card(BaseModel):
    name: str
    number: PaymentCardNumber
    exp: date

    @property
    def brand(self) -> PaymentCardBrand:
        return self.number.brand

    @property
    def expired(self) -> bool:
        return self.exp < date.today()

def last_day_of_month(year: int, month: int) -> date:
    day = calendar.monthrange(year, month)[1]
    return date(year, month, day)

card = Card(
    name='Georg Wilhelm Friedrich Hegel',
    number='4000000000000002',
    exp=last_day_of_month(2023, 9)
)

assert card.number.brand == PaymentCardBrand.visa
assert card.number.bin == '400000'
assert card.number.last4 == '0002'
assert card.number.masked == '400000******0002'
