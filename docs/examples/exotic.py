from pathlib import Path
from uuid import UUID

from pydantic import (DSN, BaseModel, EmailStr, NameEmail, PyObject, conint,
                      constr, PositiveInt, NegativeInt)


class Model(BaseModel):
    cos_function: PyObject = None
    path_to_something: Path = None

    short_str: constr(min_length=2, max_length=10) = None
    regex_str: constr(regex='apple (pie|tart|sandwich)') = None

    big_int: conint(gt=1000, lt=1024) = None
    pos_int: PositiveInt = None
    neg_int: NegativeInt = None

    email_address: EmailStr = None
    email_and_name: NameEmail = None

    db_name = 'foobar'
    db_user = 'postgres'
    db_password: str = None
    db_host = 'localhost'
    db_port = '5432'
    db_driver = 'postgres'
    db_query: dict = None
    dsn: DSN = None
    uuid: UUID = None

m = Model(
    cos_function='math.cos',
    path_to_something='/home',
    short_str='foo',
    regex_str='apple pie',
    big_int=1001,
    pos_int=1,
    neg_int=-1,
    email_address='Samuel Colvin <s@muelcolvin.com >',
    email_and_name='Samuel Colvin <s@muelcolvin.com >',
    uuid='ebcdab58-6eb8-46fb-a190-d07a33e9eac8'
)
print(m.dict())
"""
{
    'cos_function': <built-in function cos>,
    'path_to_something': PosixPath('/home'),
    'short_str': 'foo', 'regex_str': 'apple pie',
    'big_int': 1001,
    'pos_int': 1,
    'neg_int': -1,
    'email_address': 's@muelcolvin.com',
    'email_and_name': <NameEmail("Samuel Colvin <s@muelcolvin.com>")>,
    ...
    'dsn': 'postgres://postgres@localhost:5432/foobar',
    'uuid': UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'),
}
"""
