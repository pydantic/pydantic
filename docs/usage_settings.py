from pydantic import DSN, BaseSettings, PyObject


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

    class Config:
        fields = {
            'auth_key': {
                'alias': 'API_KEY'
            }
        }
