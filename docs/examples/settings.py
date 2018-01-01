from typing import Set

from pydantic import BaseModel, DSN, BaseSettings, PyObject


class SubModel(BaseModel):
    foo = 'bar'
    apple = 1


class Settings(BaseSettings):
    redis_host = 'localhost'
    redis_port = 6379
    redis_database = 0
    redis_password: str = None

    auth_key: str = ...

    invoicing_cls: PyObject = 'path.to.Invoice'

    db_name = 'foobar'
    db_user = 'postgres'
    db_password: str = None
    db_host = 'localhost'
    db_port = '5432'
    db_driver = 'postgres'
    db_query: dict = None
    dsn: DSN = None

    # to override domains:
    # export MY_PREFIX_DOMAINS = '["foo.com", "bar.com"]'
    domains: Set[str] = set()

    # to override more_settings:
    # export MY_PREFIX_MORE_SETTINGS = '{"foo": "x", "apple": 1}'
    more_settings: SubModel = SubModel()

    class Config:
        env_prefix = 'MY_PREFIX_'  # defaults to 'APP_'
        fields = {
            'auth_key': {
                'alias': 'my_api_key'
            }
        }
