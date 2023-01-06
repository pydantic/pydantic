from datetime import datetime

from pydantic import ValidationError
from pydantic.dataclasses import dataclass


class MyConfig:
    str_max_length = 10
    validate_assignment = True


@dataclass(config=MyConfig)
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
try:
    user.name = 'x' * 20
except ValidationError as e:
    print(e)
