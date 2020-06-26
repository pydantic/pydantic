from datetime import date, timedelta
from pydantic import BaseModel
from pydantic.validators import int_validator


class DayThisYear(date):
    """
    Contrived example of a special type of date that
    takes an int and interprets it as a day in the current year
    """

    @classmethod
    def __get_validators__(cls):
        yield int_validator
        yield cls.validate

    @classmethod
    def validate(cls, v: int):
        return date.today().replace(month=1, day=1) + timedelta(days=v)


class FooModel(BaseModel):
    date: DayThisYear


m = FooModel(date=300)
print(m.json())
