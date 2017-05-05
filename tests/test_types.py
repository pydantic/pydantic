import os

import pytest

from pydantic import DSN, BaseModel, Module, ValidationError, constr


class ConStringModel(BaseModel):
    v: constr(max_length=10) = 'foobar'


def test_constrained_str_good():
    m = ConStringModel(v='short')
    assert m.v == 'short'


def test_constrained_str_default():
    m = ConStringModel()
    assert m.v == 'foobar'


def test_constrained_str_too_long():
    with pytest.raises(ValidationError) as exc_info:
        ConStringModel(v='this is too long')
    assert exc_info.value.args[0] == ('1 errors validating input: {"v": {'
                                      '"msg": "length greater than maximum allowed: 10", '
                                      '"type": "ValueError", '
                                      '"validator": "ConstrainedStr.validate"}}')


class DsnModel(BaseModel):
    db_name = 'foobar'
    db_user = 'postgres'
    db_password: str = None
    db_host = 'localhost'
    db_port = '5432'
    db_driver = 'postgres'
    db_query: dict = None
    dsn: DSN = None


def test_dsn_compute():
    m = DsnModel()
    assert m.dsn == 'postgres://postgres@localhost:5432/foobar'


def test_dsn_define():
    m = DsnModel(dsn='postgres://postgres@localhost:5432/different')
    assert m.dsn == 'postgres://postgres@localhost:5432/different'


def test_dsn_pw_host():
    m = DsnModel(db_password='pword', db_host='before:after', db_query={'v': 1})
    assert m.dsn == 'postgres://postgres:pword@[before:after]:5432/foobar?v=1'


class ModuleModel(BaseModel):
    module: Module = 'os.path'


def test_module_import():
    m = ModuleModel()
    assert m.module == os.path


class CheckModel(BaseModel):
    bool_check = True
    str_check = 's'
    bytes_check = b's'
    int_check = 1
    float_check = 1.0

    class Config:
        max_anystr_length = 10
        max_number_size = 100


@pytest.mark.parametrize('field,value,result', [
    ('bool_check', True, True),
    ('bool_check', False, False),
    ('bool_check', None, False),
    ('bool_check', '', False),
    ('bool_check', 1, True),
    ('bool_check', 'TRUE', True),
    ('bool_check', b'TRUE', True),
    ('bool_check', 'true', True),
    ('bool_check', '1', True),
    ('bool_check', '2', False),
    ('bool_check', 'yes', False),
    ('bool_check', 2, True),

    ('str_check', 's', 's'),
    ('str_check', b's', 's'),
    ('str_check', 1, '1'),
    ('str_check', 'x' * 11, ValidationError),
    ('str_check', b'x' * 11, ValidationError),

    ('bytes_check', 's', b's'),
    ('bytes_check', b's', b's'),
    ('bytes_check', 1, b'1'),
    ('bytes_check', 'x' * 11, ValidationError),
    ('bytes_check', b'x' * 11, ValidationError),

    ('int_check', 1, 1),
    ('int_check', 1.9, 1),
    ('int_check', '1', 1),
    ('int_check', '1.9', ValidationError),
    ('int_check', b'1', 1),
    ('int_check', 12, 12),
    ('int_check', '12', 12),
    ('int_check', b'12', 12),
    ('int_check', 123, ValidationError),
    ('int_check', '123', ValidationError),
    ('int_check', b'123', ValidationError),

    ('float_check', 1, 1.0),
    ('float_check', 1.0, 1.0),
    ('float_check', '1.0', 1.0),
    ('float_check', '1', 1.0),
    ('float_check', b'1.0', 1.0),
    ('float_check', b'1', 1.0),
    ('float_check', 123, ValidationError),
    ('float_check', '123', ValidationError),
    ('float_check', b'123', ValidationError),
])
def test_bool_validation(field, value, result):
    kwargs = {field: value}
    if result == ValidationError:
        with pytest.raises(ValidationError):
            CheckModel(**kwargs)
    else:
        assert CheckModel(**kwargs).values[field] == result
