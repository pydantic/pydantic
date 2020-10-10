"""
Test pydantic's compliance with mypy.

Do a little skipping about with types to demonstrate its usage.
"""
import json
import sys
from datetime import date, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, NoneStr, PyObject, StrictBool, root_validator, validate_arguments, validator
from pydantic.fields import Field
from pydantic.generics import GenericModel


class Flags(BaseModel):
    strict_bool: StrictBool = False

    def __str__(self) -> str:
        return f'flag={self.strict_bool}'


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: NoneStr = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]

    @validator('age')
    def check_age(cls, value: int) -> int:
        assert value < 100, 'too old'
        return value

    @root_validator
    def root_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        return values

    @root_validator(pre=True, allow_reuse=False, skip_on_failure=False)
    def pre_root_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        return values


def dog_years(age: int) -> int:
    return age * 7


def day_of_week(dt: datetime) -> int:
    return dt.date().isoweekday()


m = Model(age=21, list_of_ints=[1, '2', b'3'])

assert m.age == 21, m.age
m.age = 42
assert m.age == 42, m.age
assert m.first_name == 'John', m.first_name
assert m.last_name is None, m.last_name
assert m.list_of_ints == [1, 2, 3], m.list_of_ints

dog_age = dog_years(m.age)
assert dog_age == 294, dog_age


m = Model(age=2, first_name=b'Woof', last_name=b'Woof', signup_ts='2017-06-07 00:00', list_of_ints=[1, '2', b'3'])

assert m.first_name == 'Woof', m.first_name
assert m.last_name == 'Woof', m.last_name
assert m.signup_ts == datetime(2017, 6, 7), m.signup_ts
assert day_of_week(m.signup_ts) == 3


data = {'age': 10, 'first_name': 'Alena', 'last_name': 'Sousova', 'list_of_ints': [410]}
m_from_obj = Model.parse_obj(data)

assert isinstance(m_from_obj, Model)
assert m_from_obj.age == 10
assert m_from_obj.first_name == data['first_name']
assert m_from_obj.last_name == data['last_name']
assert m_from_obj.list_of_ints == data['list_of_ints']

m_from_raw = Model.parse_raw(json.dumps(data))

assert isinstance(m_from_raw, Model)
assert m_from_raw.age == m_from_obj.age
assert m_from_raw.first_name == m_from_obj.first_name
assert m_from_raw.last_name == m_from_obj.last_name
assert m_from_raw.list_of_ints == m_from_obj.list_of_ints

m_copy = m_from_obj.copy()

assert isinstance(m_from_raw, Model)
assert m_copy.age == m_from_obj.age
assert m_copy.first_name == m_from_obj.first_name
assert m_copy.last_name == m_from_obj.last_name
assert m_copy.list_of_ints == m_from_obj.list_of_ints


if sys.version_info >= (3, 7):
    T = TypeVar('T')

    class WrapperModel(GenericModel, Generic[T]):
        payload: T

    int_instance = WrapperModel[int](payload=1)
    int_instance.payload += 1
    assert int_instance.payload == 2

    str_instance = WrapperModel[str](payload='a')
    str_instance.payload += 'a'
    assert str_instance.payload == 'aa'

    model_instance = WrapperModel[Model](payload=m)
    model_instance.payload.list_of_ints.append(4)
    assert model_instance.payload.list_of_ints == [1, 2, 3, 4]


class WithField(BaseModel):
    age: int
    first_name: str = Field('John', const=True)


@validate_arguments
def foo(a: int, *, c: str = 'x') -> str:
    return c * a


foo(1, c='thing')
foo(1)


class MyConf(BaseModel):
    str_pyobject: PyObject = Field('datetime.date')
    callable_pyobject: PyObject = Field(date)


conf = MyConf()
var1: date = conf.str_pyobject(2020, 12, 20)
var2: date = conf.callable_pyobject(2111, 1, 1)
