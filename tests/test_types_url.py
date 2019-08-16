import pytest

from pydantic import AnyUrl, BaseModel, HttpUrl, ValidationError
from pydantic.types import PostgresDsn, RedisDsn


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
    ],
)
def test_any_url_success(value):
    class Model(BaseModel):
        v: AnyUrl

    assert Model(v=value).v == value, value


@pytest.mark.parametrize(
    'value,err_type,err_msg,err_ctx',
    [
        ('http:///example.com/', 'value_error.url.host', 'URL host invalid', None),
        ('https:///example.com/', 'value_error.url.host', 'URL host invalid', None),
        ('http://.example.com:8000/foo', 'value_error.url.host', 'URL host invalid', None),
        (
            'https://example.org\\',
            'value_error.url.extra',
            "URL invalid, extra characters found after valid URL: '\\\\'",
            {'extra': '\\'},
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
        # https://www.xudongz.com/blog/2017/idn-phishing/ this should really be accepted but converted to punycode,
        # but that is not yet implemented.
        (
            'https://www.аррӏе.com/',
            'value_error.url.extra',
            "URL invalid, extra characters found after valid URL: 'аррӏе.com/'",
            {'extra': 'аррӏе.com/'},
        ),
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


def test_any_str_obj():
    class Model(BaseModel):
        v: AnyUrl

    url = Model(v='http://example.org').v
    assert str(url) == 'http://example.org'
    assert repr(url) == "<AnyUrl('http://example.org' scheme='http' host='example.org')>"
    assert url.scheme == 'http'
    assert url.host == 'example.org'
    assert url.port is None

    url2 = Model(v='http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit').v
    assert str(url2) == 'http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit'
    assert repr(url2) == (
        "<AnyUrl('http://user:password@example.org:1234/the/path/?query=here#fragment=is;this=bit' "
        "scheme='http' user='user:password' host='example.org' port='1234' path='/the/path/' query='query=here' "
        "fragment='fragment=is;this=bit')>"
    )
    assert url2.scheme == 'http'
    assert url2.user == 'user:password'
    assert url2.host == 'example.org'
    assert url2.port == '1234'
    assert url2.path == '/the/path/'
    assert url2.query == 'query=here'
    assert url2.fragment == 'fragment=is;this=bit'


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'HTTP://EXAMPLE.ORG',
        'https://example.org',
        'https://example.org?a=1&b=2',
        'https://example.org#a=3;b=3',
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
    ],
)
def test_http_url_invalid(value, err_type, err_msg, err_ctx):
    class Model(BaseModel):
        v: HttpUrl

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert len(exc_info.value.errors()) == 1, exc_info.value.errors()
    error = exc_info.value.errors()[0]
    debug(error)
    assert error['type'] == err_type, value
    assert error['msg'] == err_msg, value
    assert error.get('ctx') == err_ctx, value


def test_coerse_url():
    class Model(BaseModel):
        v: HttpUrl

    assert Model(v='  https://www.example.com \n').v == 'https://www.example.com'
    assert Model(v=b'https://www.example.com').v == 'https://www.example.com'


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

    assert Model(a='redis://user:pass@localhost:5432/app').a == 'redis://user:pass@localhost:5432/app'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='http://example.org')
    assert exc_info.value.errors()[0]['type'] == 'value_error.url.scheme'
