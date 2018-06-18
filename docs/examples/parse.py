import pickle
from datetime import datetime
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: datetime = None

m = User.parse_obj({'id': 123, 'name': 'James'})
print(m)
# > User id=123 name='James' signup_ts=None

try:
    User.parse_obj(['not', 'a', 'dict'])
except ValidationError as e:
    print(e)
# > error validating input
# > User expected dict not list (error_type=TypeError)

m = User.parse_raw('{"id": 123, "name": "James"}')  # assumes json as no content type passed
print(m)
# > User id=123 name='James' signup_ts=None

pickle_data = pickle.dumps({'id': 123, 'name': 'James', 'signup_ts': datetime(2017, 7, 14)})
m = User.parse_raw(pickle_data, content_type='application/pickle', allow_pickle=True)
print(m)
# > User id=123 name='James' signup_ts=datetime.datetime(2017, 7, 14, 0, 0)
