import pickle
from pathlib import Path
from datetime import datetime
import msgpack
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

msgpack_data = msgpack.packb({'id': 123, 'name': 'James', 'signup_ts': 1500000000})
m = User.parse_raw(msgpack_data, content_type='application/msgpack')
print(m)
# > User id=123 name='James' signup_ts=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc)


pickle_data = pickle.dumps({'id': 123, 'name': 'James', 'signup_ts': datetime(2017, 7, 14)})
m = User.parse_raw(pickle_data, content_type='application/pickle', allow_pickle=True)
print(m)
# > User id=123 name='James' signup_ts=datetime.datetime(2017, 7, 14, 0, 0)


Path('/tmp/data.mp').write_bytes(msgpack_data)
# data.json: {"id": 123, "name": "James"}
m = User.parse_file('/tmp/data.mp')
print(m)
# > User id=123 name='James' signup_ts=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc)
