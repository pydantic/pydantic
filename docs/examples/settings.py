from typing import Set

from devtools import debug
from pydantic import BaseModel, BaseSettings, PyObject, RedisDsn, PostgresDsn, Field

class SubModel(BaseModel):
    foo = 'bar'
    apple = 1

class Settings(BaseSettings):
    auth_key: str
    api_key: str = Field(..., env='my_api_key')

    redis_dsn: RedisDsn = 'redis://user:pass@localhost:6379/1'
    pg_dsn: PostgresDsn = 'postgres://user:pass@localhost:5432/foobar'

    special_function: PyObject = 'math.cos'

    # to override domains:
    # export my_prefix_domains='["foo.com", "bar.com"]'
    domains: Set[str] = set()

    # to override more_settings:
    # export my_prefix_more_settings='{"foo": "x", "apple": 1}'
    more_settings: SubModel = SubModel()

    class Config:
        env_prefix = 'my_prefix_'  # defaults to no prefix, e.g. ""
        fields = {
            'auth_key': {
                'env': 'my_auth_key',
            },
            'redis_dsn': {
                'env': ['service_redis_dsn', 'redis_url']
            }
        }

"""
When calling with
my_auth_key=a \
MY_API_KEY=b \
my_prefix_domains='["foo.com", "bar.com"]' \
python docs/examples/settings.py 
"""
debug(Settings().dict())
"""
docs/examples/settings.py:45 <module>
  Settings().dict(): {
    'auth_key': 'a',
    'api_key': 'b',
    'redis_dsn': <RedisDsn('redis://user:pass@localhost:6379/1' scheme='redis' ...)>,
    'pg_dsn': <PostgresDsn('postgres://user:pass@localhost:5432/foobar' scheme='postgres' ...)>,
    'special_function': <built-in function cos>,
    'domains': {'bar.com', 'foo.com'},
    'more_settings': {'foo': 'bar', 'apple': 1},
  } (dict) len=7
"""
