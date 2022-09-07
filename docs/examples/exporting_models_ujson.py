from datetime import datetime
import ujson
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: datetime = None

    class Config:
        json_loads = ujson.loads


user = User.parse_raw('{"id": 123,"signup_ts":1234567890,"name":"John Doe"}')
print(user)
