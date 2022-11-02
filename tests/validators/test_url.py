import pytest
from dirty_equals import HasRepr, IsInstance

from pydantic_core import SchemaValidator, Url, ValidationError, core_schema

from ..conftest import PyAndJson


def test_url_ok(py_and_json: PyAndJson):
    v = py_and_json(core_schema.url_schema())
    url: Url = v.validate_test('https://example.com/foo/bar?baz=qux#quux')
    assert isinstance(url, Url)
    assert str(url) == 'https://example.com/foo/bar?baz=qux#quux'
    assert repr(url) == "Url('https://example.com/foo/bar?baz=qux#quux')"
    assert url.unicode_string() == 'https://example.com/foo/bar?baz=qux#quux'
    assert url.scheme == 'https'
    assert url.host == 'example.com'
    assert url.unicode_host() == 'example.com'
    assert url.path == '/foo/bar'
    assert url.query == 'baz=qux'
    assert url.query_params() == [('baz', 'qux')]
    assert url.fragment == 'quux'
    assert url.username is None
    assert url.password is None
    assert url.port is None
    assert url.host_type == 'domain'


@pytest.mark.parametrize(
    'url,error',
    [
        ('xxx', 'relative URL without a base'),
        ('http://', 'empty host'),
        ('https://xn---', 'invalid international domain name'),
        ('http://example.com:65536', 'invalid port number'),
        ('http://1...1', 'invalid IPv4 address'),
        ('https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334[', 'invalid IPv6 address'),
        ('https://[', 'invalid IPv6 address'),
        ('https://example com', 'invalid domain character'),
        ('http://exam%ple.com', 'invalid domain character'),
        ('/more', 'relative URL without a base'),
    ],
)
def test_url_error(py_and_json: PyAndJson, url, error):
    v = py_and_json(core_schema.url_schema())

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test(url)
    assert exc_info.value.error_count() == 1
    assert exc_info.value.errors()[0]['ctx']['error'] == error


@pytest.mark.parametrize(
    'input_value,expected,host_type',
    [
        ('http://example.com', 'http://example.com/', 'domain'),
        ('http://example.com./foobar', 'http://example.com./foobar', 'domain'),
        # works since we're in lax mode
        (b'http://example.com', 'http://example.com/', 'domain'),
        ('https://£££.com', 'https://xn--9aaa.com/', 'punycode_domain'),
        ('https://foobar.£££.com', 'https://foobar.xn--9aaa.com/', 'punycode_domain'),
        ('https://foo.£$.money.com', 'https://foo.xn--$-9ba.money.com/', 'punycode_domain'),
        ('https://xn--9aaa.com/', 'https://xn--9aaa.com/', 'punycode_domain'),
        ('https://münchen/', 'https://xn--mnchen-3ya/', 'punycode_domain'),
        ('ssh://xn--9aaa.com/', 'ssh://xn--9aaa.com/', 'domain'),
        ('ssh://münchen.com/', 'ssh://m%C3%BCnchen.com/', 'domain'),
        ('ssh://example/', 'ssh://example/', 'domain'),
        ('ssh://£££/', 'ssh://%C2%A3%C2%A3%C2%A3/', 'domain'),
        ('ssh://%C2%A3%C2%A3%C2%A3/', 'ssh://%C2%A3%C2%A3%C2%A3/', 'domain'),
        ('http://à.א̈.com', 'http://xn--0ca.xn--ssa73l.com/', 'punycode_domain'),
        ('ftp://127.0.0.1', 'ftp://127.0.0.1/', 'ipv4'),
        ('wss://1.1.1.1', 'wss://1.1.1.1/', 'ipv4'),
        ('ftp://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]', 'ftp://[2001:db8:85a3::8a2e:370:7334]/', 'ipv6'),
        ('https:/more', 'https://more/', 'domain'),
        ('https:more', 'https://more/', 'domain'),
        ('file:///foobar', 'file:///foobar', None),
    ],
)
def test_host_types(input_value, expected, host_type):
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python(input_value)
    assert isinstance(url, Url)
    assert str(url) == expected
    assert url.host_type == host_type


@pytest.mark.parametrize(
    'input_value,host,unicode_host',
    [
        ('http://example.com', 'example.com', 'example.com'),
        ('http://example.com.', 'example.com.', 'example.com.'),
        (b'http://example.com', 'example.com', 'example.com'),
        ('https://£££.com', 'xn--9aaa.com', '£££.com'),
        ('https://£££.com.', 'xn--9aaa.com.', '£££.com.'),
        ('https://xn--9aaa.com/', 'xn--9aaa.com', '£££.com'),
        ('https://münchen/', 'xn--mnchen-3ya', 'münchen'),
        ('http://à.א̈.com', 'xn--0ca.xn--ssa73l.com', 'à.א̈.com'),
        ('ftp://xn--0ca.xn--ssa73l.com', 'xn--0ca.xn--ssa73l.com', 'à.א̈.com'),
        ('https://foobar.£££.com/', 'foobar.xn--9aaa.com', 'foobar.£££.com'),
        ('wss://1.1.1.1', '1.1.1.1', '1.1.1.1'),
        (
            'ftp://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]',
            '[2001:db8:85a3::8a2e:370:7334]',
            '[2001:db8:85a3::8a2e:370:7334]',
        ),
        ('file:///foobar', None, None),
    ],
)
def test_unicode_hosts(input_value, host, unicode_host):
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python(input_value)
    assert isinstance(url, Url)
    assert url.host == host
    assert url.unicode_host() == unicode_host


@pytest.mark.parametrize(
    'input_value,unicode_string',
    [
        ('http://example.com', 'http://example.com/'),
        ('https://£££.com', 'https://£££.com/'),
        ('https://xn--9aaa.com/', 'https://£££.com/'),
        ('https://münchen/', 'https://münchen/'),
        ('wss://1.1.1.1', 'wss://1.1.1.1/'),
        ('file:///foobar', 'file:///foobar'),
    ],
)
def test_unicode_domain(input_value, unicode_string):
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python(input_value)
    assert url.unicode_string() == unicode_string


def test_host_required():
    v = SchemaValidator(core_schema.url_schema(host_required=True))
    url = v.validate_python('http://example.com')
    assert url.host == 'example.com'
    with pytest.raises(ValidationError, match=r'URL host required \[type=url_host_required,'):
        v.validate_python('unix:/run/foo.socket')


def test_no_host():
    v = SchemaValidator(core_schema.url_schema())
    url = v.validate_python('data:text/plain,Stuff')
    assert str(url) == 'data:text/plain,Stuff'
    assert url.host is None
    assert url.scheme == 'data'
    assert url.path == 'text/plain,Stuff'


def test_max_length():
    v = SchemaValidator(core_schema.url_schema(max_length=25))
    assert str(v.validate_python('https://example.com')) == 'https://example.com/'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('https://example.com/foo/bar')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'url_too_long',
            'loc': (),
            'msg': 'URL should have at most 25 characters',
            'input': 'https://example.com/foo/bar',
            'ctx': {'max_length': 25},
        }
    ]


def test_allowed_schemes_ok():
    v = SchemaValidator(core_schema.url_schema(allowed_schemes=['http', 'https']))
    url = v.validate_python(' https://example.com ')
    assert url.host == 'example.com'
    assert url.scheme == 'https'
    assert str(url) == 'https://example.com/'
    assert str(v.validate_python('http://other.com')) == 'http://other.com/'


def test_allowed_schemes_error():
    v = SchemaValidator(core_schema.url_schema(allowed_schemes=['http', 'https']))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('unix:/run/foo.socket')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'url_schema',
            'loc': (),
            'msg': "URL schema should be 'http' or 'https'",
            'input': 'unix:/run/foo.socket',
            'ctx': {'expected_schemas': "'http' or 'https'"},
        }
    ]


def test_allowed_schemes_errors():
    v = SchemaValidator(core_schema.url_schema(allowed_schemes=['a', 'b', 'c']))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('unix:/run/foo.socket')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'url_schema',
            'loc': (),
            'msg': "URL schema should be 'a', 'b' or 'c'",
            'input': 'unix:/run/foo.socket',
            'ctx': {'expected_schemas': "'a', 'b' or 'c'"},
        }
    ]


def test_url_query_repeat():
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python('https://example.com/foo/bar?a=1&a=2')
    assert str(url) == 'https://example.com/foo/bar?a=1&a=2'
    assert url.query_params() == [('a', '1'), ('a', '2')]


def test_url_to_url():
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python('https://example.com')
    assert str(url) == 'https://example.com/'
    url2 = v.validate_python(url)
    assert str(url2) == 'https://example.com/'
    assert url is not url2


def test_url_to_constraint():
    v1 = SchemaValidator(core_schema.url_schema())
    url: Url = v1.validate_python('http://example.com/foobar/bar')
    assert str(url) == 'http://example.com/foobar/bar'

    v2 = SchemaValidator(core_schema.url_schema(max_length=25))

    with pytest.raises(ValidationError) as exc_info:
        v2.validate_python(url)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'url_too_long',
            'loc': (),
            'msg': 'URL should have at most 25 characters',
            'input': IsInstance(Url) & HasRepr("Url('http://example.com/foobar/bar')"),
            'ctx': {'max_length': 25},
        }
    ]

    v3 = SchemaValidator(core_schema.url_schema(allowed_schemes=['https']))

    with pytest.raises(ValidationError) as exc_info:
        v3.validate_python(url)
    assert exc_info.value.errors() == [
        {
            'type': 'url_schema',
            'loc': (),
            'msg': "URL schema should be 'https'",
            'input': IsInstance(Url) & HasRepr("Url('http://example.com/foobar/bar')"),
            'ctx': {'expected_schemas': "'https'"},
        }
    ]


def test_wrong_type_lax():
    v = SchemaValidator(core_schema.url_schema())
    assert str(v.validate_python('http://example.com/foobar/bar')) == 'http://example.com/foobar/bar'
    assert str(v.validate_python(b'http://example.com/foobar/bar')) == 'http://example.com/foobar/bar'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        v.validate_python(123)

    # runtime strict
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        v.validate_python(b'http://example.com/foobar/bar', strict=True)


def test_wrong_type_strict():
    v = SchemaValidator(core_schema.url_schema(), {'strict': True})
    url = v.validate_python('http://example.com/foobar/bar')
    assert str(url) == 'http://example.com/foobar/bar'
    assert str(v.validate_python(url)) == 'http://example.com/foobar/bar'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        v.validate_python(b'http://example.com/foobar/bar')
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        v.validate_python(123)


@pytest.mark.parametrize(
    'input_value,expected,username,password',
    [
        ('https://apple:pie@example.com/foo', 'https://apple:pie@example.com/foo', 'apple', 'pie'),
        ('https://apple:@example.com/foo', 'https://apple@example.com/foo', 'apple', None),
        ('https://app$le:pie@example.com/foo', 'https://app$le:pie@example.com/foo', 'app$le', 'pie'),
        ('https://app le:pie@example.com/foo', 'https://app%20le:pie@example.com/foo', 'app%20le', 'pie'),
    ],
)
def test_username(input_value, expected, username, password):
    v = SchemaValidator(core_schema.url_schema())
    url: Url = v.validate_python(input_value)
    assert isinstance(url, Url)
    assert str(url) == expected
    assert url.username == username
    assert url.password == password
