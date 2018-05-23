import os
from typing import Union

import pytest

from pydantic.utils import display_as_type, import_string, make_dsn, to_snake_case, validate_email

try:
    import email_validator
except ImportError:
    email_validator = None


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize('value,name,email', [
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
    ('чебурашкаящик-с-апельсинами.рф@example.com',
     'чебурашкаящик-с-апельсинами.рф',
     'чебурашкаящик-с-апельсинами.рф@example.com'),
    ('उदाहरण.परीक्ष@domain.with.idn.tld', 'उदाहरण.परीक्ष', 'उदाहरण.परीक्ष@domain.with.idn.tld'),
    ('foo.bar@example.com', 'foo.bar', 'foo.bar@example.com'),
    ('foo.bar@exam-ple.com ', 'foo.bar', 'foo.bar@exam-ple.com'),
    ('ιωάννης@εεττ.gr', 'ιωάννης', 'ιωάννης@εεττ.gr'),
])
def test_address_valid(value, name, email):
    assert validate_email(value) == (name, email)


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
@pytest.mark.parametrize('value', [
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
])
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


@pytest.mark.parametrize('value,expected', (
    (str, 'str'),
    ('string', 'str'),
    (Union[str, int], 'typing.Union[str, int]'),
))
def test_display_as_type(value, expected):
    assert display_as_type(value) == expected


@pytest.mark.parametrize('value,expected', (
    ('Foo', 'foo'),
    ('FooBar', 'foo_bar'),
    ('Foo42Bar', 'foo42_bar'),
    ('FOOBar', 'foo_bar'),
    ('FOOBarFoo', 'foo_bar_foo'),
    ('FooBAR', 'foo_bar'),
    ('FOO', 'foo'),
))
def test_to_snake_case(value, expected):
    assert to_snake_case(value) == expected
