import uuid
from pathlib import Path
from uuid import UUID

from pydantic import (DSN, UUID1, UUID3, UUID4, UUID5, BaseModel, EmailStr, NameEmail, NegativeFloat, NegativeInt,
                      PositiveFloat, PositiveInt, PyObject, confloat, conint, constr)


class Model(BaseModel):
    cos_function: PyObject = None
    path_to_something: Path = None

    short_str: constr(min_length=2, max_length=10) = None
    regex_str: constr(regex='apple (pie|tart|sandwich)') = None
    strip_str: constr(strip_whitespace=True)

    big_int: conint(gt=1000, lt=1024) = None
    pos_int: PositiveInt = None
    neg_int: NegativeInt = None

    big_float: confloat(gt=1000, lt=1024) = None
    pos_float: PositiveFloat = None
    neg_float: NegativeFloat = None

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
    uuid_any: UUID = None
    uuid_v1: UUID1 = None
    uuid_v3: UUID3 = None
    uuid_v4: UUID4 = None
    uuid_v5: UUID5 = None

m = Model(
    cos_function='math.cos',
    path_to_something='/home',
    short_str='foo',
    regex_str='apple pie',
    strip_str='   bar',
    big_int=1001,
    pos_int=1,
    neg_int=-1,
    big_float=1002.1,
    pos_float=2.2,
    neg_float=-2.3,
    email_address='Samuel Colvin <s@muelcolvin.com >',
    email_and_name='Samuel Colvin <s@muelcolvin.com >',
    uuid_any=uuid.uuid4(),
    uuid_v1=uuid.uuid1(),
    uuid_v3=uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'),
    uuid_v4=uuid.uuid4(),
    uuid_v5=uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
)
print(m.dict())
"""
{
    'cos_function': <built-in function cos>,
    'path_to_something': PosixPath('/home'),
    'short_str': 'foo',
    'regex_str': 'apple pie',
    'strip_str': 'bar',
    'big_int': 1001,
    'pos_int': 1,
    'neg_int': -1,
    'big_float': 1002.1,
    'pos_float': 2.2,
    'neg_float': -2.3,
    'email_address': 's@muelcolvin.com',
    'email_and_name': <NameEmail("Samuel Colvin <s@muelcolvin.com>")>,
    ...
    'dsn': 'postgres://postgres@localhost:5432/foobar',
    'uuid_any': UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'),
    'uuid_v1': UUID('c96e505c-4c62-11e8-a27c-dca90496b483'),
    'uuid_v3': UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e'),
    'uuid_v4': UUID('22209f7a-aad1-491c-bb83-ea19b906d210'),
    'uuid_v5': UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d'),
}
"""
