import os
from enum import Enum
from typing import NewType, Union

import pytest

from pydantic.utils import (
    ValueItems,
    display_as_type,
    import_string,
    is_new_type,
    lenient_issubclass,
    make_dsn,
    new_type_supertype,
    truncate,
    validate_email,
)

try:
    import email_validator
except ImportError:
    email_validator = None


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize(
    'value,name,email',
    [
        ('foobar@example.com', 'foobar', 'foobar@example.com'),
        ('s@muelcolvin.com', 's', 's@muelcolvin.com'),
        ('Samuel Colvin <s@muelcolvin.com>', 'Samuel Colvin', 's@muelcolvin.com'),
        ('foobar <foobar@example.com>', 'foobar', 'foobar@example.com'),
        (' foo.bar@example.com', 'foo.bar', 'foo.bar@example.com'),
        ('foo.bar@example.com ', 'foo.bar', 'foo.bar@example.com'),
        ('foo BAR <foobar@example.com >', 'foo BAR', 'foobar@example.com'),
        ('FOO bar   <foobar@example.com> ', 'FOO bar', 'foobar@example.com'),
        ('<FOOBAR@example.com> ', 'FOOBAR', 'foobar@example.com'),
        ('ñoñó@example.com', 'ñoñó', 'ñoñó@example.com'),
        ('我買@example.com', '我買', '我買@example.com'),
        ('甲斐黒川日本@example.com', '甲斐黒川日本', '甲斐黒川日本@example.com'),
        (
            'чебурашкаящик-с-апельсинами.рф@example.com',
            'чебурашкаящик-с-апельсинами.рф',
            'чебурашкаящик-с-апельсинами.рф@example.com',
        ),
        ('उदाहरण.परीक्ष@domain.with.idn.tld', 'उदाहरण.परीक्ष', 'उदाहरण.परीक्ष@domain.with.idn.tld'),
        ('foo.bar@example.com', 'foo.bar', 'foo.bar@example.com'),
        ('foo.bar@exam-ple.com ', 'foo.bar', 'foo.bar@exam-ple.com'),
        ('ιωάννης@εεττ.gr', 'ιωάννης', 'ιωάννης@εεττ.gr'),
    ],
)
def test_address_valid(value, name, email):
    assert validate_email(value) == (name, email)


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize(
    'value',
    [
        'f oo.bar@example.com ',
        'foo.bar@exam\nple.com ',
        'foobar',
        'foobar <foobar@example.com',
        '@example.com',
        'foobar@.example.com',
        'foobar@.com',
        'foo bar@example.com',
        'foo@bar@example.com',
        '\n@example.com',
        '\r@example.com',
        '\f@example.com',
        ' @example.com',
        '\u0020@example.com',
        '\u001f@example.com',
        '"@example.com',
        '\"@example.com',
        ',@example.com',
        'foobar <foobar<@example.com>',
    ],
)
def test_address_invalid(value):
    with pytest.raises(ValueError):
        validate_email(value)


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed():
    with pytest.raises(ImportError):
        validate_email('s@muelcolvin.com')


def test_empty_dsn():
    assert make_dsn(driver='foobar') == 'foobar://'


def test_dsn_odd_user():
    assert make_dsn(driver='foobar', user='foo@bar') == 'foobar://foo%40bar@'


def test_import_module():
    assert import_string('os.path') == os.path


def test_import_module_invalid():
    with pytest.raises(ImportError) as exc_info:
        import_string('xx')
    assert exc_info.value.args[0] == '"xx" doesn\'t look like a module path'


def test_import_no_attr():
    with pytest.raises(ImportError) as exc_info:
        import_string('os.foobar')
    assert exc_info.value.args[0] == 'Module "os" does not define a "foobar" attribute'


@pytest.mark.parametrize(
    'value,expected', ((str, 'str'), ('string', 'str'), (Union[str, int], 'typing.Union[str, int]'))
)
def test_display_as_type(value, expected):
    assert display_as_type(value) == expected


def test_display_as_type_enum():
    class SubField(Enum):
        a = 1
        b = 'b'

    displayed = display_as_type(SubField)
    assert displayed == 'enum'


def test_display_as_type_enum_int():
    class SubField(int, Enum):
        a = 1
        b = 2

    displayed = display_as_type(SubField)
    assert displayed == 'int'


def test_display_as_type_enum_str():
    class SubField(str, Enum):
        a = 'a'
        b = 'b'

    displayed = display_as_type(SubField)
    assert displayed == 'str'


def test_lenient_issubclass():
    class A(str):
        pass

    assert lenient_issubclass(A, str) is True


def test_lenient_issubclass_is_lenient():
    assert lenient_issubclass('a', 'a') is False


def test_truncate_type():
    assert truncate(object) == "<class 'object'>"


def test_value_items():
    v = ['a', 'b', 'c']
    vi = ValueItems(v, {0, -1})
    assert vi.is_excluded(2)
    assert [v_ for i, v_ in enumerate(v) if not vi.is_excluded(i)] == ['b']

    assert vi.is_included(2)
    assert [v_ for i, v_ in enumerate(v) if vi.is_included(i)] == ['a', 'c']

    v2 = {'a': v, 'b': {'a': 1, 'b': (1, 2)}, 'c': 1}

    vi = ValueItems(v2, {'a': {0, -1}, 'b': {'a': ..., 'b': -1}})

    assert not vi.is_excluded('a')
    assert vi.is_included('a')
    assert not vi.is_excluded('c')
    assert not vi.is_included('c')

    assert str(vi) == "ValueItems: dict({'a': {0, -1}, 'b': {'a': Ellipsis, 'b': -1}})"

    excluded = {k_: v_ for k_, v_ in v2.items() if not vi.is_excluded(k_)}
    assert excluded == {'a': v, 'b': {'a': 1, 'b': (1, 2)}, 'c': 1}

    included = {k_: v_ for k_, v_ in v2.items() if vi.is_included(k_)}
    assert included == {'a': v, 'b': {'a': 1, 'b': (1, 2)}}

    sub_v = included['a']
    sub_vi = ValueItems(sub_v, vi.for_element('a'))
    assert str(sub_vi) == 'ValueItems: set({0, 2})'

    assert sub_vi.is_excluded(2)
    assert [v_ for i, v_ in enumerate(sub_v) if not sub_vi.is_excluded(i)] == ['b']

    assert sub_vi.is_included(2)
    assert [v_ for i, v_ in enumerate(sub_v) if sub_vi.is_included(i)] == ['a', 'c']


def test_value_items_error():
    with pytest.raises(ValueError) as e:
        ValueItems(1, (1, 2, 3))

    assert str(e.value) == "Unexpected type of exclude value <class 'tuple'>"


def test_is_new_type():
    new_type = NewType('new_type', str)
    new_new_type = NewType('new_new_type', new_type)
    assert is_new_type(new_type)
    assert is_new_type(new_new_type)
    assert not is_new_type(str)


def test_new_type_supertype():
    new_type = NewType('new_type', str)
    new_new_type = NewType('new_new_type', new_type)
    assert new_type_supertype(new_type) == str
    assert new_type_supertype(new_new_type) == str
