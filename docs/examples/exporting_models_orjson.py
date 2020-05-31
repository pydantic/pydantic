from datetime import datetime
import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: datetime = None

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


user = User.parse_raw('{"id":123,"signup_ts":1234567890,"name":"John Doe"}')
print(user.json())
