import pytest

from pydantic import AnyUrl, BaseModel, EmailStr, HttpUrl, NameEmail, PostgresDsn, RedisDsn, ValidationError, stricturl
from pydantic.networks import validate_email

try:
    import email_validator
except ImportError:
    email_validator = None


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'http://test',
        'http://localhost',
        'https://example.org/whatever/next/',
        'postgres://user:pass@localhost:5432/app',
        'postgres://just-user@localhost:5432/app',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/hatch',
        'foo-bar://example.org',
        'foo.bar://example.org',
        'foo0bar://example.org',
        'https://example.org',
        'http://localhost',
        'http://localhost/',
        'http://localhost:8000',
        'http://localhost:8000/',
        'https://foo_bar.example.com/',
        'ftp://example.org',
        'ftps://example.org',
        'http://example.co.jp',
        'http://www.example.com/a%C2%B1b',
        'http://www.example.com/~username/',
        'http://info.example.com?fred',
        'http://info.example.com/?fred',
        'http://xn--mgbh0fb.xn--kgbechtv/',
        'http://example.com/blue/red%3Fand+green',
        'http://www.example.com/?array%5Bkey%5D=value',
        'http://xn--rsum-bpad.example.org/',
        'http://123.45.67.8/',
        'http://123.45.67.8:8329/',
        'http://[2001:db8::ff00:42]:8329',
        'http://[2001::1]:8329',
        'http://[2001:db8::1]/',
        'http://www.example.com:8000/foo',
        'http://www.cwi.nl:80/%7Eguido/Python.html',
        'https://www.python.org/путь',
        'http://андрей@example.com',
        AnyUrl('https://example.com', scheme='https', host='example.com'),
        'https://exam_ple.com/',
        'http://twitter.com/@handle/',
    ],
)
def test_any_url_success(value):
    class Model(BaseModel):
        v: AnyUrl

    assert Model(v=value).v, value


@pytest.mark.parametrize(
    'value,err_type,err_msg,err_ctx',
    [
        ('http:///example.com/', 'value_error.url.host', 'URL host invalid', None),
        ('https:///example.com/', 'value_error.url.host', 'URL host invalid', None),
        ('http://.example.com:8000/foo', 'value_error.url.host', 'URL host invalid', None),
        ('https://example.org\\', 'value_error.url.host', 'URL host invalid', None),
        ('https://exampl$e.org', 'value_error.url.host', 'URL host invalid', None),
        ('http://??', 'value_error.url.host', 'URL host invalid', None),
        ('http://.', 'value_error.url.host', 'URL host invalid', None),
        ('http://..', 'value_error.url.host', 'URL host invalid', None),
        (
            'https://example.org more',
            'value_error.url.extra',
            "URL invalid, extra characters found after valid URL: ' more'",
            {'extra': ' more'},
        ),
        ('$https://example.org', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('../icons/logo.gif', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('abc', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('..', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('/', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('+http://example.com/', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        ('ht*tp://example.com/', 'value_error.url.scheme', 'invalid or missing URL scheme', None),
        (' ', 'value_error.any_str.min_length', 'ensure this value has at least 1 characters', {'limit_value': 1}),
        ('', 'value_error.any_str.min_length', 'ensure this value has at least 1 characters', {'limit_value': 1}),
        (None, 'type_error.none.not_allowed', 'none is not an allowed value', None),
        (
            'http://2001:db8::ff00:42:8329',
            'value_error.url.extra',
            "URL invalid, extra characters found after valid URL: ':db8::ff00:42:8329'",
            {'extra': ':db8::ff00:42:8329'},
        ),
        ('http://[192.168.1.1]:8329', 'value_error.url.host', 'URL host invalid', None),
        ('http://example.com:99999', 'value_error.url.port', 'URL port invalid, port cannot exceed 65535', None),
    ],
)
def test_any_url_invalid(value, err_type, err_msg, err_ctx):
    class Model(BaseModel):
        v: AnyUrl

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert len(exc_info.value.errors()) == 1, exc_info.value.errors()
    error = exc_info.value.errors()[0]
    # debug(error)
    assert error['type'] == err_type, value
    assert error['msg'] == err_msg, value
    assert error.get('ctx') == err_ctx, value


def validate_url(s):
    class Model(BaseModel):
        v: AnyUrl

    return Model(v=s).v


def test_any_url_parts():
    url = validate_url('http://example.org')
    assert str(url) == 'http://example.org'
    assert repr(url) == "AnyUrl('http://example.org', scheme='http', host='example.org', tld='org', host_type='domain')"
    assert url.scheme == 'http'
    assert url.host == 'example.org'
    assert url.tld == 'org'
    assert url.host_type == 'domain'
    assert url.port is None
    assert url == AnyUrl('http://example.org', scheme='https', host='example.org')


def test_url_repr():
    url = validate_url('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit')
    assert str(url) == 'http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit'
    assert repr(url) == (
        "AnyUrl('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit', "
        "scheme='http', user='user', password='password', host='example.org', tld='org', host_type='domain', "
        "port='1234', path='/the/path/', query='query=here', fragment='fragment=is;this=bit')"
    )
    assert url.scheme == 'http'
    assert url.user == 'user'
    assert url.password == 'password'
    assert url.host == 'example.org'
    assert url.host_type == 'domain'
    assert url.port == '1234'
    assert url.path == '/the/path/'
    assert url.query == 'query=here'
    assert url.fragment == 'fragment=is;this=bit'


def test_ipv4_port():
    url = validate_url('ftp://123.45.67.8:8329/')
    assert url.scheme == 'ftp'
    assert url.host == '123.45.67.8'
    assert url.host_type == 'ipv4'
    assert url.port == '8329'
    assert url.user is None
    assert url.password is None


def test_ipv6_port():
    url = validate_url('wss://[2001:db8::ff00:42]:8329')
    assert url.scheme == 'wss'
    assert url.host == '[2001:db8::ff00:42]'
    assert url.host_type == 'ipv6'
    assert url.port == '8329'


def test_int_domain():
    url = validate_url('https://£££.org')
    assert url.host == 'xn--9aaa.org'
    assert url.host_type == 'int_domain'
    assert str(url) == 'https://xn--9aaa.org'


def test_co_uk():
    url = validate_url('http://example.co.uk')
    assert str(url) == 'http://example.co.uk'
    assert url.scheme == 'http'
    assert url.host == 'example.co.uk'
    assert url.tld == 'uk'  # wrong but no better solution
    assert url.host_type == 'domain'


def test_user_no_password():
    url = validate_url('http://user:@example.org')
    assert url.user == 'user'
    assert url.password == ''
    assert url.host == 'example.org'


def test_user_info_no_user():
    url = validate_url('http://:password@example.org')
    assert url.user == ''
    assert url.password == 'password'
    assert url.host == 'example.org'


def test_at_in_path():
    url = validate_url('https://twitter.com/@handle')
    assert url.scheme == 'https'
    assert url.host == 'twitter.com'
    assert url.user is None
    assert url.password is None
    assert url.path == '/@handle'


def test_fragment_without_query():
    url = validate_url('https://pydantic-docs.helpmanual.io/usage/types/#constrained-types')
    assert url.scheme == 'https'
    assert url.host == 'pydantic-docs.helpmanual.io'
    assert url.path == '/usage/types/'
    assert url.query is None
    assert url.fragment == 'constrained-types'


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'http://example.org/foobar',
        'http://example.org.',
        'http://example.org./foobar',
        'HTTP://EXAMPLE.ORG',
        'https://example.org',
        'https://example.org?a=1&b=2',
        'https://example.org#a=3;b=3',
        'https://foo_bar.example.com/',
        'https://exam_ple.com/',  # should perhaps fail? I think it's contrary to the RFC but chrome allows it
        'https://example.xn--p1ai',
        'https://example.xn--vermgensberatung-pwb',
        'https://example.xn--zfr164b',
    ],
)
def test_http_url_success(value):
    class Model(BaseModel):
        v: HttpUrl

    assert Model(v=value).v == value, value


@pytest.mark.parametrize(
    'value,err_type,err_msg,err_ctx',
    [
        (
            'ftp://example.com/',
            'value_error.url.scheme',
            'URL scheme not permitted',
            {'allowed_schemes': {'https', 'http'}},
        ),
        ('http://foobar/', 'value_error.url.host', 'URL host invalid, top level domain required', None),
        ('http://localhost/', 'value_error.url.host', 'URL host invalid, top level domain required', None),
        ('https://example.123', 'value_error.url.host', 'URL host invalid, top level domain required', None),
        ('https://example.ab123', 'value_error.url.host', 'URL host invalid, top level domain required', None),
        (
            'x' * 2084,
            'value_error.any_str.max_length',
            'ensure this value has at most 2083 characters',
            {'limit_value': 2083},
        ),
    ],
)
def test_http_url_invalid(value, err_type, err_msg, err_ctx):
    class Model(BaseModel):
        v: HttpUrl

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert len(exc_info.value.errors()) == 1, exc_info.value.errors()
    error = exc_info.value.errors()[0]
    assert error['type'] == err_type, value
    assert error['msg'] == err_msg, value
    assert error.get('ctx') == err_ctx, value


@pytest.mark.parametrize(
    'input,output',
    [
        ('  https://www.example.com \n', 'https://www.example.com'),
        (b'https://www.example.com', 'https://www.example.com'),
        # https://www.xudongz.com/blog/2017/idn-phishing/ accepted but converted
        ('https://www.аррӏе.com/', 'https://www.xn--80ak6aa92e.com/'),
        ('https://exampl£e.org', 'https://xn--example-gia.org'),
        ('https://example.珠宝', 'https://example.xn--pbt977c'),
        ('https://example.vermögensberatung', 'https://example.xn--vermgensberatung-pwb'),
        ('https://example.рф', 'https://example.xn--p1ai'),
        ('https://exampl£e.珠宝', 'https://xn--example-gia.xn--pbt977c'),
    ],
)
def test_coerse_url(input, output):
    class Model(BaseModel):
        v: HttpUrl

    assert Model(v=input).v == output


@pytest.mark.parametrize(
    'input,output',
    [
        ('  https://www.example.com \n', 'com'),
        (b'https://www.example.com', 'com'),
        ('https://www.example.com?param=value', 'com'),
        ('https://example.珠宝', 'xn--pbt977c'),
        ('https://exampl£e.珠宝', 'xn--pbt977c'),
        ('https://example.vermögensberatung', 'xn--vermgensberatung-pwb'),
        ('https://example.рф', 'xn--p1ai'),
        ('https://example.рф?param=value', 'xn--p1ai'),
    ],
)
def test_parses_tld(input, output):
    class Model(BaseModel):
        v: HttpUrl

    assert Model(v=input).v.tld == output


def test_postgres_dsns():
    class Model(BaseModel):
        a: PostgresDsn

    assert Model(a='postgres://user:pass@localhost:5432/app').a == 'postgres://user:pass@localhost:5432/app'
    assert Model(a='postgresql://user:pass@localhost:5432/app').a == 'postgresql://user:pass@localhost:5432/app'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors()[0]['type'] == 'value_error.url.scheme'
    assert exc_info.value.json().startswith('[')

    with pytest.raises(ValidationError) as exc_info:
        Model(a='postgres://localhost:5432/app')
    error = exc_info.value.errors()[0]
    assert error == {'loc': ('a',), 'msg': 'userinfo required in URL but missing', 'type': 'value_error.url.userinfo'}


def test_redis_dsns():
    class Model(BaseModel):
        a: RedisDsn

    m = Model(a='redis://user:pass@localhost:1234/app')
    assert m.a == 'redis://user:pass@localhost:1234/app'
    assert m.a.user == 'user'
    assert m.a.password == 'pass'

    m = Model(a='rediss://user:pass@localhost:1234/app')
    assert m.a == 'rediss://user:pass@localhost:1234/app'

    m = Model(a='rediss://:pass@localhost:1234')
    assert m.a == 'rediss://:pass@localhost:1234/0'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors()[0]['type'] == 'value_error.url.scheme'

    # Password is not required for Redis protocol
    m = Model(a='redis://localhost:1234/app')
    assert m.a == 'redis://localhost:1234/app'
    assert m.a.user is None
    assert m.a.password is None

    # Only schema is required for Redis protocol. Otherwise it will be set to default
    # https://www.iana.org/assignments/uri-schemes/prov/redis
    m = Model(a='rediss://')
    assert m.a.scheme == 'rediss'
    assert m.a.host == 'localhost'
    assert m.a.port == '6379'
    assert m.a.path == '/0'


def test_custom_schemes():
    class Model(BaseModel):
        v: stricturl(strip_whitespace=False, allowed_schemes={'ws', 'wss'})  # noqa: F821

    assert Model(v='ws://example.org').v == 'ws://example.org'

    with pytest.raises(ValidationError):
        Model(v='http://example.org')

    with pytest.raises(ValidationError):
        Model(v='ws://example.org  ')


@pytest.mark.parametrize(
    'kwargs,expected',
    [
        (dict(scheme='ws', user='foo', host='example.net'), 'ws://foo@example.net'),
        (dict(scheme='ws', user='foo', password='x', host='example.net'), 'ws://foo:x@example.net'),
        (dict(scheme='ws', host='example.net', query='a=b', fragment='c=d'), 'ws://example.net?a=b#c=d'),
        (dict(scheme='http', host='example.net', port='1234'), 'http://example.net:1234'),
    ],
)
def test_build_url(kwargs, expected):
    assert AnyUrl(None, **kwargs) == expected


def test_son():
    class Model(BaseModel):
        v: HttpUrl

    m = Model(v='http://foo@example.net')
    assert m.json() == '{"v": "http://foo@example.net"}'
    assert m.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'minLength': 1, 'maxLength': 2083, 'type': 'string', 'format': 'uri'}},
        'required': ['v'],
    }


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
        ('<FOOBAR@example.com> ', 'FOOBAR', 'FOOBAR@example.com'),
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


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_email_str():
    class Model(BaseModel):
        v: EmailStr

    assert Model(v=EmailStr('foo@example.org')).v == 'foo@example.org'
    assert Model(v='foo@example.org').v == 'foo@example.org'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_name_email():
    class Model(BaseModel):
        v: NameEmail

    assert str(Model(v=NameEmail('foo bar', 'foobaR@example.com')).v) == 'foo bar <foobaR@example.com>'
    assert str(Model(v='foo bar  <foobaR@example.com>').v) == 'foo bar <foobaR@example.com>'
    assert NameEmail('foo bar', 'foobaR@example.com') == NameEmail('foo bar', 'foobaR@example.com')
    assert NameEmail('foo bar', 'foobaR@example.com') != NameEmail('foo bar', 'different@example.com')
