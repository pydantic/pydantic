from typing import List, Optional

from pydantic import BaseModel


class Address(BaseModel):
    city: str
    country: str


class User(BaseModel):
    name: str
    address: Address
    friends: Optional[List['User']] = None

    class Config:
        json_encoders = {
            Address: lambda a: f'{a.city} ({a.country})',
            'User': lambda u: f'{u.name} in {u.address.city} '
                              f'({u.address.country[:2].upper()})',
        }


User.update_forward_refs()

wolfgang = User(
    name='Wolfgang',
    address=Address(city='Berlin', country='Deutschland'),
    friends=[
        User(name='Pierre', address=Address(city='Paris', country='France')),
        User(name='John', address=Address(city='London', country='UK')),
    ],
)
print(wolfgang.json(models_as_dict=False))
