import pytest

from pydantic.utils import validate_email


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
])
def test_address_valid(value, name, email):
    assert validate_email(value) == (name, email)


@pytest.mark.parametrize('value', [
    'f oo.bar@example.com ',
    'foo.bar@exam\nple.com ',
    'foobar',
    'foobar <foobar@example.com',
    '@example.com',
    'foobar@example.co-m',
    'foobar@.example.com',
    'foobar@.com',
    'test@domain.with.idn.tld.उदाहरण.परीक्षा',
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
    '`@example.com',
    ',@example.com',
    'foobar <foobar`@example.com>',
])
def test_address_invalid(value):
    with pytest.raises(ValueError):
        validate_email(value)
