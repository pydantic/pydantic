import pytest

from pydantic import AnyUrl, BaseModel, HttpUrl, PostgresDsn, RedisDsn, ValidationError, stricturl
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


def test_any_url_obj():
    class Model(BaseModel):
        v: AnyUrl

    url = Model(v='http://example.org').v
    assert str(url) == 'http://example.org'
    assert repr(url) == "AnyUrl('http://example.org' scheme='http' host='example.org' tld='org' host_type='domain')"
    assert url.scheme == 'http'
    assert url.host == 'example.org'
    assert url.tld == 'org'
    assert url.host_type == 'domain'
    assert url.port is None
    assert url == AnyUrl('http://example.org', scheme='https', host='example.org')

    url2 = Model(v='http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit').v
    assert str(url2) == 'http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit'
    assert repr(url2) == (
        "AnyUrl('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit' "
        "scheme='http' user='user' password='password' host='example.org' tld='org' host_type='domain' port='1234' "
        "path='/the/path/' query='query=here' fragment='fragment=is;this=bit')"
    )
    assert url2.scheme == 'http'
    assert url2.user == 'user'
    assert url2.password == 'password'
    assert url2.host == 'example.org'
    assert url.host_type == 'domain'
    assert url2.port == '1234'
    assert url2.path == '/the/path/'
    assert url2.query == 'query=here'
    assert url2.fragment == 'fragment=is;this=bit'

    url3 = Model(v='ftp://123.45.67.8:8329/').v
    assert url3.scheme == 'ftp'
    assert url3.host == '123.45.67.8'
    assert url3.host_type == 'ipv4'
    assert url3.port == '8329'
    assert url3.user is None
    assert url3.password is None

    url4 = Model(v='wss://[2001:db8::ff00:42]:8329').v
    assert url4.scheme == 'wss'
    assert url4.host == '[2001:db8::ff00:42]'
    assert url4.host_type == 'ipv6'
    assert url4.port == '8329'

    url5 = Model(v='https://£££.org').v
    assert url5.host == 'xn--9aaa.org'
    assert url5.host_type == 'int_domain'
    assert str(url5) == 'https://xn--9aaa.org'

    url6 = Model(v='http://example.co.uk').v
    assert str(url6) == 'http://example.co.uk'
    assert url6.scheme == 'http'
    assert url6.host == 'example.co.uk'
    assert url6.tld == 'uk'  # wrong but no better solution
    assert url6.host_type == 'domain'

    url7 = Model(v='http://user:@example.org').v
    assert url7.user == 'user'
    assert url7.password == ''
    assert url7.host == 'example.org'


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
    ],
)
def test_coerse_url(input, output):
    class Model(BaseModel):
        v: HttpUrl

    assert Model(v=input).v == output


def test_postgres_dsns():
    class Model(BaseModel):
        a: PostgresDsn

    assert Model(a='postgres://user:pass@localhost:5432/app').a == 'postgres://user:pass@localhost:5432/app'
    assert Model(a='postgresql://user:pass@localhost:5432/app').a == 'postgresql://user:pass@localhost:5432/app'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors()[0]['type'] == 'value_error.url.scheme'


def test_redis_dsns():
    class Model(BaseModel):
        a: RedisDsn

    m = Model(a='redis://user:pass@localhost:5432/app')
    assert m.a == 'redis://user:pass@localhost:5432/app'
    assert m.a.user == 'user'
    assert m.a.password == 'pass'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors()[0]['type'] == 'value_error.url.scheme'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='redis://localhost:5432/app')
    error = exc_info.value.errors()[0]
    assert error == {'loc': ('a',), 'msg': 'userinfo required in URL but missing', 'type': 'value_error.url.userinfo'}


def test_custom_schemes():
    class Model(BaseModel):
        v: stricturl(strip_whitespace=False, allowed_schemes={'ws', 'wss'})

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
