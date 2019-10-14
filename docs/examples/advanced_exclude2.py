import datetime
from typing import List

from pydantic import BaseModel, SecretStr

class Country(BaseModel):
    name: str
    phone_code: int

class Address(BaseModel):
    post_code: int
    country: Country

class CardDetails(BaseModel):
    number: SecretStr
    expires: datetime.date

class Hobby(BaseModel):
    name: str
    info: str

class User(BaseModel):
    first_name: str
    second_name: str
    address: Address
    card_details: CardDetails
    hobbies: List[Hobby]

user = User(
    first_name='John',
    second_name='Doe',
    address=Address(
        post_code=123456,
        country=Country(
            name='USA',
            phone_code=1
        )
    ),
    card_details=CardDetails(
        number=4212934504460000,
        expires=datetime.date(2020, 5, 1)
    ),
    hobbies=[
        Hobby(name='Programming', info='Writing code and stuff'),
        Hobby(name='Gaming', info='Hell Yeah!!!')
    ]

)

exclude_keys = {
    'second_name': ...,
    'address': {'post_code': ..., 'country': {'phone_code'}},
    'card_details': ...,
    # You can exclude values from tuples and lists by indexes
    'hobbies': {-1: {'info'}},
}

include_keys = {
    'first_name': ...,
    'address': {'country': {'name'}},
    'hobbies': {0: ..., -1: {'name'}}
}

print(
    user.dict(include=include_keys) == user.dict(exclude=exclude_keys) == {
        'first_name': 'John',
        'address': {'country': {'name': 'USA'}},
        'hobbies': [
            {'name': 'Programming', 'info': 'Writing code and stuff'},
            {'name': 'Gaming'}
        ]
    }
)
