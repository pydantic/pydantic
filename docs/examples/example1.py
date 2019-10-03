from datetime import datetime
from typing import List
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: datetime = None
    friends: List[int] = []

external_data = {
    'id': '123',
    'signup_ts': '2019-06-01 12:22',
    'friends': [1, '2', 3.1415]
}
user = User(**external_data)
print(user.id)
#> 123
print(repr(user.signup_ts))
#> datetime.datetime(2019, 6, 1, 12, 22)
print(user.friends)
#> [1, 2, 3]
print(user.dict())
#> {
#>     'id': 123,
#>     'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
#>     'friends': [1, 2, 3],
#>     'name': 'John Doe'
#> }
print(user.json())
#> {"id": 123, "signup_ts": "2019-06-01T12:22:00", ...
