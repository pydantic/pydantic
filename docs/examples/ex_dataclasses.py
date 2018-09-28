from datetime import datetime
from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
# > User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
