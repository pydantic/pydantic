import pytest
from dirty_equals import HasRepr, IsInstance

from pydantic_core import SchemaValidator, Url, ValidationError, core_schema

from ..conftest import Err, PyAndJson


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


@pytest.fixture(scope='module', name='url_validator')
def url_validator_fixture():
    return SchemaValidator(core_schema.url_schema())


@pytest.mark.parametrize(
    'url,expected',
    [
        (
            'http://example.com',
            {
                'str()': 'http://example.com/',
                'host_type': 'domain',
                'host': 'example.com',
                'unicode_host()': 'example.com',
                'unicode_string()': 'http://example.com/',
            },
        ),
        ('http://exa\nmple.com', {'str()': 'http://example.com/', 'host_type': 'domain', 'host': 'example.com'}),
        ('xxx', Err('relative URL without a base')),
        ('http://', Err('empty host')),
        ('https://xn---', Err('invalid international domain name')),
        ('http://example.com:65536', Err('invalid port number')),
        ('http://1...1', Err('invalid IPv4 address')),
        ('https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334[', Err('invalid IPv6 address')),
        ('https://[', Err('invalid IPv6 address')),
        ('https://example com', Err('invalid domain character')),
        ('http://exam%ple.com', Err('invalid domain character')),
        ('http:// /', Err('invalid domain character')),
        ('/more', Err('relative URL without a base')),
        ('http://example.com./foobar', {'str()': 'http://example.com./foobar', 'host_type': 'domain'}),
        # works since we're in lax mode
        (
            b'http://example.com',
            {'str()': 'http://example.com/', 'host_type': 'domain', 'unicode_host()': 'example.com'},
        ),
        ('http:/foo', {'str()': 'http://foo/', 'host_type': 'domain'}),
        ('http:///foo', {'str()': 'http://foo/', 'host_type': 'domain'}),
        ('http://exam_ple.com', {'str()': 'http://exam_ple.com/', 'host_type': 'domain'}),
        ('http://exam-ple.com', {'str()': 'http://exam-ple.com/', 'host_type': 'domain'}),
        ('http://example-.com', {'str()': 'http://example-.com/', 'host_type': 'domain'}),
        ('https://£££.com', {'str()': 'https://xn--9aaa.com/', 'host_type': 'punycode_domain'}),
        ('https://foobar.£££.com', {'str()': 'https://foobar.xn--9aaa.com/', 'host_type': 'punycode_domain'}),
        ('https://foo.£$.money.com', {'str()': 'https://foo.xn--$-9ba.money.com/', 'host_type': 'punycode_domain'}),
        ('https://xn--9aaa.com/', {'str()': 'https://xn--9aaa.com/', 'host_type': 'punycode_domain'}),
        ('https://münchen/', {'str()': 'https://xn--mnchen-3ya/', 'host_type': 'punycode_domain'}),
        ('http://à.א̈.com', {'str()': 'http://xn--0ca.xn--ssa73l.com/', 'host_type': 'punycode_domain'}),
        ('ssh://xn--9aaa.com/', 'ssh://xn--9aaa.com/'),
        ('ssh://münchen.com/', 'ssh://m%C3%BCnchen.com/'),
        ('ssh://example/', 'ssh://example/'),
        ('ssh://£££/', 'ssh://%C2%A3%C2%A3%C2%A3/'),
        ('ssh://%C2%A3%C2%A3%C2%A3/', 'ssh://%C2%A3%C2%A3%C2%A3/'),
        ('ftp://127.0.0.1', {'str()': 'ftp://127.0.0.1/', 'host_type': 'ipv4'}),
        (
            'wss://1.1.1.1',
            {'str()': 'wss://1.1.1.1/', 'host_type': 'ipv4', 'host': '1.1.1.1', 'unicode_host()': '1.1.1.1'},
        ),
        (
            'ftp://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]',
            {
                'str()': 'ftp://[2001:db8:85a3::8a2e:370:7334]/',
                'host_type': 'ipv6',
                'host': '[2001:db8:85a3::8a2e:370:7334]',
                'unicode_host()': '[2001:db8:85a3::8a2e:370:7334]',
            },
        ),
        ('https:/more', {'str()': 'https://more/', 'host': 'more'}),
        ('https:more', {'str()': 'https://more/', 'host': 'more'}),
        ('file:///foobar', {'str()': 'file:///foobar', 'host_type': None, 'host': None, 'unicode_host()': None}),
        ('file:///:80', {'str()': 'file:///:80', 'host_type': None}),
        ('file://:80', Err('invalid domain character')),
        ('foobar://:80', Err('empty host')),
        ('mongodb+srv://server.example.com/', 'mongodb+srv://server.example.com/'),
        ('http://example.com.', {'host': 'example.com.', 'unicode_host()': 'example.com.'}),
        ('http:/example.com', {'host': 'example.com', 'unicode_host()': 'example.com'}),
        ('http:/foo', {'host': 'foo', 'unicode_host()': 'foo'}),
        ('http://foo', {'host': 'foo', 'unicode_host()': 'foo'}),
        ('http:///foo', {'host': 'foo', 'unicode_host()': 'foo'}),
        ('http:////foo', {'host': 'foo', 'unicode_host()': 'foo'}),
        ('http://-', {'host': '-', 'unicode_host()': '-'}),
        ('http:////example.com', {'host': 'example.com', 'unicode_host()': 'example.com'}),
        ('https://£££.com', {'host': 'xn--9aaa.com', 'unicode_host()': '£££.com'}),
        ('https://£££.com.', {'host': 'xn--9aaa.com.', 'unicode_host()': '£££.com.'}),
        ('https://xn--9aaa.com/', {'host': 'xn--9aaa.com', 'unicode_host()': '£££.com'}),
        ('https://münchen/', {'host': 'xn--mnchen-3ya', 'unicode_host()': 'münchen'}),
        ('http://à.א̈.com', {'host': 'xn--0ca.xn--ssa73l.com', 'unicode_host()': 'à.א̈.com'}),
        ('ftp://xn--0ca.xn--ssa73l.com', {'host': 'xn--0ca.xn--ssa73l.com', 'unicode_host()': 'à.א̈.com'}),
        ('https://foobar.£££.com/', {'host': 'foobar.xn--9aaa.com', 'unicode_host()': 'foobar.£££.com'}),
        ('https://£££.com', {'unicode_string()': 'https://£££.com/'}),
        ('https://xn--9aaa.com/', {'unicode_string()': 'https://£££.com/'}),
        ('https://münchen/', {'unicode_string()': 'https://münchen/'}),
        ('wss://1.1.1.1', {'unicode_string()': 'wss://1.1.1.1/'}),
        ('file:///foobar', {'unicode_string()': 'file:///foobar'}),
    ],
)
def test_url_error(url_validator, url, expected):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            url_validator.validate_python(url)
        assert exc_info.value.error_count() == 1
        error = exc_info.value.errors()[0]
        assert error['type'] == 'url_parsing'
        assert error['ctx']['error'] == expected.message
    else:
        output_url = url_validator.validate_python(url)
        assert isinstance(output_url, Url)
        if isinstance(expected, str):
            assert str(output_url) == expected
        else:
            assert isinstance(expected, dict)
            output_parts = {}
            for key in expected:
                if key == 'str()':
                    output_parts[key] = str(output_url)
                elif key.endswith('()'):
                    output_parts[key] = getattr(output_url, key[:-2])()
                else:
                    output_parts[key] = getattr(output_url, key)
            assert output_parts == expected


@pytest.fixture(scope='module', name='strict_url_validator')
def strict_url_validator_fixture():
    return SchemaValidator(core_schema.url_schema(), {'strict': True})


@pytest.mark.parametrize(
    'url,expected',
    [
        ('http://example.com', {'str()': 'http://example.com/', 'host_type': 'domain', 'host': 'example.com'}),
        ('http://exa\nmple.com', Err('tabs or newlines are ignored in URLs', 'url_syntax_violation')),
        ('xxx', Err('relative URL without a base', 'url_parsing')),
        ('http:/foo', Err('expected //', 'url_syntax_violation')),
        ('http:///foo', Err('expected //', 'url_syntax_violation')),
        ('http:////foo', Err('expected //', 'url_syntax_violation')),
        ('http://exam_ple.com', {'str()': 'http://exam_ple.com/', 'host_type': 'domain'}),
        ('https:/more', Err('expected //', 'url_syntax_violation')),
        ('https:more', Err('expected //', 'url_syntax_violation')),
        ('file:///foobar', {'str()': 'file:///foobar', 'host_type': None, 'host': None, 'unicode_host()': None}),
        ('file://:80', Err('invalid domain character', 'url_parsing')),
        ('file:/xx', Err('expected // after file:', 'url_syntax_violation')),
        ('foobar://:80', Err('empty host', 'url_parsing')),
        ('mongodb+srv://server.example.com/', 'mongodb+srv://server.example.com/'),
    ],
)
def test_url_error_strict(strict_url_validator, url, expected):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            strict_url_validator.validate_python(url)
        assert exc_info.value.error_count() == 1
        error = exc_info.value.errors()[0]
        assert error['ctx']['error'] == expected.message
        assert error['type'] == expected.errors
    else:
        output_url = strict_url_validator.validate_python(url)
        assert isinstance(output_url, Url)
        if isinstance(expected, str):
            assert str(output_url) == expected
        else:
            assert isinstance(expected, dict)
            output_parts = {}
            for key in expected:
                if key == 'str()':
                    output_parts[key] = str(output_url)
                elif key.endswith('()'):
                    output_parts[key] = getattr(output_url, key[:-2])()
                else:
                    output_parts[key] = getattr(output_url, key)
            assert output_parts == expected


def test_host_required():
    v = SchemaValidator(core_schema.url_schema(host_required=True))
    url = v.validate_python('http://example.com')
    assert url.host == 'example.com'
    with pytest.raises(ValidationError, match=r'URL host required \[type=url_host_required,'):
        v.validate_python('unix:/run/foo.socket')


def test_no_host(url_validator):
    url = url_validator.validate_python('data:text/plain,Stuff')
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


def test_url_query_repeat(url_validator):
    url: Url = url_validator.validate_python('https://example.com/foo/bar?a=1&a=2')
    assert str(url) == 'https://example.com/foo/bar?a=1&a=2'
    assert url.query_params() == [('a', '1'), ('a', '2')]


def test_url_to_url(url_validator):
    url: Url = url_validator.validate_python('https://example.com')
    assert str(url) == 'https://example.com/'
    url2 = url_validator.validate_python(url)
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


def test_wrong_type_lax(url_validator):
    assert str(url_validator.validate_python('http://example.com/foobar/bar')) == 'http://example.com/foobar/bar'
    assert str(url_validator.validate_python(b'http://example.com/foobar/bar')) == 'http://example.com/foobar/bar'
    with pytest.raises(ValidationError, match=r'URL input should be a string or URL \[type=url_type,'):
        url_validator.validate_python(123)

    # runtime strict
    with pytest.raises(ValidationError, match=r'URL input should be a string or URL \[type=url_type,'):
        url_validator.validate_python(b'http://example.com/foobar/bar', strict=True)


def test_wrong_type_strict(strict_url_validator):
    url = strict_url_validator.validate_python('http://example.com/foobar/bar')
    assert str(url) == 'http://example.com/foobar/bar'
    assert str(strict_url_validator.validate_python(url)) == 'http://example.com/foobar/bar'
    with pytest.raises(ValidationError, match=r'URL input should be a string or URL \[type=url_type,'):
        strict_url_validator.validate_python(b'http://example.com/foobar/bar')
    with pytest.raises(ValidationError, match=r'URL input should be a string or URL \[type=url_type,'):
        strict_url_validator.validate_python(123)


@pytest.mark.parametrize(
    'input_value,expected,username,password',
    [
        ('https://apple:pie@example.com/foo', 'https://apple:pie@example.com/foo', 'apple', 'pie'),
        ('https://apple:@example.com/foo', 'https://apple@example.com/foo', 'apple', None),
        ('https://app$le:pie@example.com/foo', 'https://app$le:pie@example.com/foo', 'app$le', 'pie'),
        ('https://app le:pie@example.com/foo', 'https://app%20le:pie@example.com/foo', 'app%20le', 'pie'),
    ],
)
def test_username(url_validator, input_value, expected, username, password):
    url: Url = url_validator.validate_python(input_value)
    assert isinstance(url, Url)
    assert str(url) == expected
    assert url.username == username
    assert url.password == password


def test_strict_not_strict(url_validator, strict_url_validator):
    url = url_validator.validate_python('http:/example.com/foobar/bar')
    assert str(url) == 'http://example.com/foobar/bar'

    url2 = strict_url_validator.validate_python(url)
    assert str(url2) == 'http://example.com/foobar/bar'
