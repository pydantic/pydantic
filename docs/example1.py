from datetime import datetime
from pydantic import BaseModel

class UserModel(BaseModel):
    id: int = ...
    name = 'John Doe'
    signup_ts: datetime = None

external_data = {'id': '123', 'signup_ts': '2017-06-01 12:22'}
user = UserModel(**external_data)
print(user)
# > UserModel id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22)
print(user.id)
# > 123
