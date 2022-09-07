# no-print-intercept
from datetime import datetime
from typing import List
from pydantic import BaseModel

from devtools import debug


class Address(BaseModel):
    street: str
    country: str
    lat: float
    lng: float


class User(BaseModel):
    id: int
    name: str
    signup_ts: datetime
    friends: List[int]
    address: Address


user = User(
    id='123',
    name='John Doe',
    signup_ts='2019-06-01 12:22',
    friends=[1234, 4567, 7890],
    address=dict(street='Testing', country='uk', lat=51.5, lng=0),
)
debug(user)
print('\nshould be much easier read than:\n')
print('user:', user)
