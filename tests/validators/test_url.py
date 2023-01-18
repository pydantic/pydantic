import re
from typing import Optional, Union

import pytest
from dirty_equals import HasRepr, IsInstance

from pydantic_core import MultiHostUrl, SchemaError, SchemaValidator, Url, ValidationError, core_schema

from ..conftest import Err, PyAndJson


def test_url_ok(py_and_json: PyAndJson):
    v = py_and_json(core_schema.url_schema())
    url = v.validate_test('https://example.com/foo/bar?baz=qux#quux')

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
    assert url.port == 443


def test_url_from_constructor_ok():
    url = Url('https://example.com/foo/bar?baz=qux#quux')

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
    assert url.port == 443


@pytest.fixture(scope='module', name='url_validator')
def url_validator_fixture():
    return SchemaValidator(core_schema.url_schema())


SCHEMA_VALIDATOR_MODE = 'SCHEMA_VALIDATOR'
URL_CLASS_MODE = 'URI_CLASS'
MULTI_URL_CLASS_MODE = 'MULTI_URL_CLASS'


def url_test_case_helper(
    url: str, expected: Union[Err, str], validator_mode: str, url_validator: Optional[SchemaValidator] = None
):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            if validator_mode == SCHEMA_VALIDATOR_MODE:
                url_validator.validate_python(url)
            elif validator_mode == URL_CLASS_MODE:
                Url(url)
            else:  # validator_mode == MULTI_URL_CLASS_MODE:
                MultiHostUrl(url)
        assert exc_info.value.error_count() == 1
        error = exc_info.value.errors()[0]
        assert error['type'] == 'url_parsing'
        assert error['ctx']['error'] == expected.message
    else:
        if validator_mode == SCHEMA_VALIDATOR_MODE:
            output_url = url_validator.validate_python(url)
        elif validator_mode == URL_CLASS_MODE:
            output_url = Url(url)
        elif validator_mode == MULTI_URL_CLASS_MODE:
            output_url = MultiHostUrl(url)
        else:
            raise ValueError(f'Unknown validator mode: {validator_mode}')
        assert isinstance(output_url, (Url, MultiHostUrl))
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


@pytest.mark.parametrize('mode', [SCHEMA_VALIDATOR_MODE, URL_CLASS_MODE])
@pytest.mark.parametrize(
    'url,expected',
    [
        (
            'http://example.com',
            {
                'str()': 'http://example.com/',
                'host': 'example.com',
                'unicode_host()': 'example.com',
                'unicode_string()': 'http://example.com/',
            },
        ),
        ('http://exa\nmple.com', {'str()': 'http://example.com/', 'host': 'example.com'}),
        ('xxx', Err('relative URL without a base')),
        ('http://', Err('empty host')),
        ('https://xn---', Err('invalid international domain name')),
        ('http://example.com:65535', 'http://example.com:65535/'),
        ('http:\\\\example.com', 'http://example.com/'),
        ('http:example.com', 'http://example.com/'),
        ('http://example.com:65536', Err('invalid port number')),
        ('http://1...1', Err('invalid IPv4 address')),
        ('https://[2001:0db8:85a3:0000:0000:8a2e:0370:7334[', Err('invalid IPv6 address')),
        ('https://[', Err('invalid IPv6 address')),
        ('https://example com', Err('invalid domain character')),
        ('http://exam%ple.com', Err('invalid domain character')),
        ('http:// /', Err('invalid domain character')),
        ('/more', Err('relative URL without a base')),
        ('http://example.com./foobar', {'str()': 'http://example.com./foobar'}),
        # works since we're in lax mode
        (b'http://example.com', {'str()': 'http://example.com/', 'unicode_host()': 'example.com'}),
        ('http:/foo', {'str()': 'http://foo/'}),
        ('http:///foo', {'str()': 'http://foo/'}),
        ('http://exam_ple.com', {'str()': 'http://exam_ple.com/'}),
        ('http://exam-ple.com', {'str()': 'http://exam-ple.com/'}),
        ('http://example-.com', {'str()': 'http://example-.com/'}),
        ('https://£££.com', {'str()': 'https://xn--9aaa.com/'}),
        ('https://foobar.£££.com', {'str()': 'https://foobar.xn--9aaa.com/'}),
        ('https://foo.£$.money.com', {'str()': 'https://foo.xn--$-9ba.money.com/'}),
        ('https://xn--9aaa.com/', {'str()': 'https://xn--9aaa.com/'}),
        ('https://münchen/', {'str()': 'https://xn--mnchen-3ya/'}),
        ('http://à.א̈.com', {'str()': 'http://xn--0ca.xn--ssa73l.com/'}),
        ('ssh://xn--9aaa.com/', 'ssh://xn--9aaa.com/'),
        ('ssh://münchen.com/', 'ssh://m%C3%BCnchen.com/'),
        ('ssh://example/', 'ssh://example/'),
        ('ssh://£££/', 'ssh://%C2%A3%C2%A3%C2%A3/'),
        ('ssh://%C2%A3%C2%A3%C2%A3/', 'ssh://%C2%A3%C2%A3%C2%A3/'),
        ('ftp://127.0.0.1', {'str()': 'ftp://127.0.0.1/', 'path': '/'}),
        ('wss://1.1.1.1', {'str()': 'wss://1.1.1.1/', 'host': '1.1.1.1', 'unicode_host()': '1.1.1.1'}),
        ('snap://[::1]', {'str()': 'snap://[::1]', 'host': '[::1]', 'unicode_host()': '[::1]'}),
        (
            'ftp://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]',
            {
                'str()': 'ftp://[2001:db8:85a3::8a2e:370:7334]/',
                'host': '[2001:db8:85a3::8a2e:370:7334]',
                'unicode_host()': '[2001:db8:85a3::8a2e:370:7334]',
            },
        ),
        ('foobar://127.0.0.1', {'str()': 'foobar://127.0.0.1', 'path': None}),
        (
            'mysql://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]',
            {'str()': 'mysql://[2001:db8:85a3::8a2e:370:7334]', 'path': None},
        ),
        (
            'mysql://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]/thing',
            {'str()': 'mysql://[2001:db8:85a3::8a2e:370:7334]/thing', 'path': '/thing'},
        ),
        ('https:/more', {'str()': 'https://more/', 'host': 'more'}),
        ('https:more', {'str()': 'https://more/', 'host': 'more'}),
        ('file:///foobar', {'str()': 'file:///foobar', 'host': None, 'unicode_host()': None}),
        ('file:///:80', {'str()': 'file:///:80'}),
        ('file://:80', Err('invalid domain character')),
        ('foobar://:80', Err('empty host')),
        # with bashslashes
        ('file:\\\\foobar\\more', {'str()': 'file://foobar/more', 'host': 'foobar', 'path': '/more'}),
        ('http:\\\\foobar\\more', {'str()': 'http://foobar/more', 'host': 'foobar', 'path': '/more'}),
        ('mongo:\\\\foobar\\more', {'str()': 'mongo:\\\\foobar\\more', 'host': None, 'path': '\\\\foobar\\more'}),
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
        (
            'https://münchen/',
            {'host': 'xn--mnchen-3ya', 'unicode_host()': 'münchen', 'unicode_string()': 'https://münchen/'},
        ),
        ('http://à.א̈.com', {'host': 'xn--0ca.xn--ssa73l.com', 'unicode_host()': 'à.א̈.com'}),
        ('ftp://xn--0ca.xn--ssa73l.com', {'host': 'xn--0ca.xn--ssa73l.com', 'unicode_host()': 'à.א̈.com'}),
        ('https://foobar.£££.com/', {'host': 'foobar.xn--9aaa.com', 'unicode_host()': 'foobar.£££.com'}),
        ('https://£££.com', {'unicode_string()': 'https://£££.com/'}),
        ('https://xn--9aaa.com/', {'unicode_string()': 'https://£££.com/'}),
        ('wss://1.1.1.1', {'unicode_string()': 'wss://1.1.1.1/'}),
        ('file:///foobar', {'unicode_string()': 'file:///foobar'}),
        (
            'postgresql+py-postgresql://user:pass@localhost:5432/app',
            {
                'str()': 'postgresql+py-postgresql://user:pass@localhost:5432/app',
                'username': 'user',
                'password': 'pass',
            },
        ),
        ('https://https/', {'host': 'https', 'unicode_host()': 'https'}),
        ('http://user:@example.org', {'str()': 'http://user@example.org/', 'username': 'user', 'password': None}),
        (
            'http://us@er:p[ass@example.org',
            {'str()': 'http://us%40er:p%5Bass@example.org/', 'username': 'us%40er', 'password': 'p%5Bass'},
        ),
        (
            'http://us%40er:p%5Bass@example.org',
            {'str()': 'http://us%40er:p%5Bass@example.org/', 'username': 'us%40er', 'password': 'p%5Bass'},
        ),
        (
            'http://us[]er:p,ass@example.org',
            {'str()': 'http://us%5B%5Der:p,ass@example.org/', 'username': 'us%5B%5Der', 'password': 'p,ass'},
        ),
        ('http://%2F:@example.org', {'str()': 'http://%2F@example.org/', 'username': '%2F', 'password': None}),
        ('foo://user:@example.org', {'str()': 'foo://user@example.org', 'username': 'user', 'password': None}),
        (
            'foo://us@er:p[ass@example.org',
            {'str()': 'foo://us%40er:p%5Bass@example.org', 'username': 'us%40er', 'password': 'p%5Bass'},
        ),
        (
            'foo://us%40er:p%5Bass@example.org',
            {'str()': 'foo://us%40er:p%5Bass@example.org', 'username': 'us%40er', 'password': 'p%5Bass'},
        ),
        (
            'foo://us[]er:p,ass@example.org',
            {'str()': 'foo://us%5B%5Der:p,ass@example.org', 'username': 'us%5B%5Der', 'password': 'p,ass'},
        ),
        ('foo://%2F:@example.org', {'str()': 'foo://%2F@example.org', 'username': '%2F', 'password': None}),
        ('HTTP://EXAMPLE.ORG', {'str()': 'http://example.org/'}),
        ('HTTP://EXAMPLE.org', {'str()': 'http://example.org/'}),
        ('POSTGRES://EXAMPLE.ORG', {'str()': 'postgres://EXAMPLE.ORG'}),
        ('https://twitter.com/@handle', {'str()': 'https://twitter.com/@handle', 'path': '/@handle'}),
        ('  https://www.example.com \n', 'https://www.example.com/'),
        # https://www.xudongz.com/blog/2017/idn-phishing/ accepted but converted
        ('https://www.аррӏе.com/', 'https://www.xn--80ak6aa92e.com/'),
        ('https://exampl£e.org', 'https://xn--example-gia.org/'),
        ('https://example.珠宝', 'https://example.xn--pbt977c/'),
        ('https://example.vermögensberatung', 'https://example.xn--vermgensberatung-pwb/'),
        ('https://example.рф', 'https://example.xn--p1ai/'),
        ('https://exampl£e.珠宝', 'https://xn--example-gia.xn--pbt977c/'),
        ('ht💣tp://example.org', Err('relative URL without a base')),
        (
            'http://usßer:pasℝs@a💣b.com:123/c?d=e&d=f#g',
            {
                'str()': 'http://us%C3%9Fer:pas%E2%84%9Ds@xn--ab-qt72a.com:123/c?d=e&d=f#g',
                'username': 'us%C3%9Fer',
                'password': 'pas%E2%84%9Ds',
                'host': 'xn--ab-qt72a.com',
                'port': 123,
                'path': '/c',
                'query': 'd=e&d=f',
                'query_params()': [('d', 'e'), ('d', 'f')],
                'fragment': 'g',
            },
        ),
    ],
)
def test_url_cases(url_validator, url, expected, mode):
    url_test_case_helper(url, expected, mode, url_validator)


@pytest.mark.parametrize(
    'validator_kwargs,url,expected',
    [
        (
            dict(default_port=1234, default_path='/baz'),
            'http://example.org',
            {'str()': 'http://example.org:1234/baz', 'host': 'example.org', 'port': 1234, 'path': '/baz'},
        ),
        (dict(default_host='localhost'), 'redis://', {'str()': 'redis://localhost', 'host': 'localhost'}),
    ],
)
def test_url_defaults_single_url(validator_kwargs, url, expected):
    s = SchemaValidator(core_schema.url_schema(**validator_kwargs))
    url_test_case_helper(url, expected, SCHEMA_VALIDATOR_MODE, s)


@pytest.mark.parametrize(
    'validator_kwargs,url,expected',
    [
        (
            dict(default_port=1234, default_path='/baz'),
            'http://example.org',
            {
                'str()': 'http://example.org:1234/baz',
                'hosts()': [{'host': 'example.org', 'password': None, 'port': 1234, 'username': None}],
                'path': '/baz',
            },
        ),
        (
            dict(default_host='localhost'),
            'redis://',
            {
                'str()': 'redis://localhost',
                'hosts()': [{'host': 'localhost', 'password': None, 'port': None, 'username': None}],
            },
        ),
        (
            {},
            'redis://localhost,127.0.0.1',
            {
                'str()': 'redis://localhost,127.0.0.1',
                'hosts()': [
                    {'host': 'localhost', 'password': None, 'port': None, 'username': None},
                    {'host': '127.0.0.1', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        ({}, 'redis://', {'str()': 'redis://', 'hosts()': []}),
    ],
)
def test_url_defaults_multi_host_url(validator_kwargs, url, expected):
    s = SchemaValidator(core_schema.multi_host_url_schema(**validator_kwargs))
    url_test_case_helper(url, expected, SCHEMA_VALIDATOR_MODE, s)


@pytest.mark.parametrize(
    'url,expected',
    [
        (
            'http://example.org:1234/baz',
            {
                'str()': 'http://example.org:1234/baz',
                'hosts()': [{'host': 'example.org', 'password': None, 'port': 1234, 'username': None}],
                'path': '/baz',
            },
        ),
        (
            'redis://localhost,127.0.0.1',
            {
                'str()': 'redis://localhost,127.0.0.1',
                'hosts()': [
                    {'host': 'localhost', 'password': None, 'port': None, 'username': None},
                    {'host': '127.0.0.1', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        ('redis://', {'str()': 'redis://', 'hosts()': []}),
    ],
)
def test_multi_host_url(url, expected):
    url_test_case_helper(url, expected, MULTI_URL_CLASS_MODE, None)


def test_multi_host_default_host_no_comma():
    with pytest.raises(SchemaError, match='default_host cannot contain a comma, see pydantic-core#326'):
        SchemaValidator(core_schema.multi_host_url_schema(default_host='foo,bar'))


@pytest.fixture(scope='module', name='strict_url_validator')
def strict_url_validator_fixture():
    return SchemaValidator(core_schema.url_schema(), {'strict': True})


@pytest.mark.parametrize(
    'url,expected',
    [
        ('http://example.com', {'str()': 'http://example.com/', 'host': 'example.com'}),
        ('http://exa\nmple.com', Err('tabs or newlines are ignored in URLs', 'url_syntax_violation')),
        ('xxx', Err('relative URL without a base', 'url_parsing')),
        ('http:/foo', Err('expected //', 'url_syntax_violation')),
        ('http:///foo', Err('expected //', 'url_syntax_violation')),
        ('http:////foo', Err('expected //', 'url_syntax_violation')),
        ('http://exam_ple.com', {'str()': 'http://exam_ple.com/'}),
        ('https:/more', Err('expected //', 'url_syntax_violation')),
        ('https:more', Err('expected //', 'url_syntax_violation')),
        ('file:///foobar', {'str()': 'file:///foobar', 'host': None, 'unicode_host()': None}),
        ('file://:80', Err('invalid domain character', 'url_parsing')),
        ('file:/xx', Err('expected // after file:', 'url_syntax_violation')),
        ('foobar://:80', Err('empty host', 'url_parsing')),
        ('mongodb+srv://server.example.com/', 'mongodb+srv://server.example.com/'),
        ('http://user:@example.org', 'http://user@example.org/'),
        ('http://us[er:@example.org', Err('non-URL code point', 'url_syntax_violation')),
        ('http://us%5Ber:bar@example.org', 'http://us%5Ber:bar@example.org/'),
        ('http://user:@example.org', 'http://user@example.org/'),
        ('mongodb://us%5Ber:bar@example.org', 'mongodb://us%5Ber:bar@example.org'),
        ('mongodb://us@er@example.org', Err('unencoded @ sign in username or password', 'url_syntax_violation')),
    ],
)
def test_url_error(strict_url_validator, url, expected):
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
            'type': 'url_scheme',
            'loc': (),
            'msg': "URL scheme should be 'http' or 'https'",
            'input': 'unix:/run/foo.socket',
            'ctx': {'expected_schemes': "'http' or 'https'"},
        }
    ]


def test_allowed_schemes_errors():
    v = SchemaValidator(core_schema.url_schema(allowed_schemes=['a', 'b', 'c']))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('unix:/run/foo.socket')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'url_scheme',
            'loc': (),
            'msg': "URL scheme should be 'a', 'b' or 'c'",
            'input': 'unix:/run/foo.socket',
            'ctx': {'expected_schemes': "'a', 'b' or 'c'"},
        }
    ]


def test_url_query_repeat(url_validator):
    url: Url = url_validator.validate_python('https://example.com/foo/bar?a=1&a=2')
    assert str(url) == 'https://example.com/foo/bar?a=1&a=2'
    assert url.query_params() == [('a', '1'), ('a', '2')]


def test_url_to_url(url_validator, multi_host_url_validator):
    url: Url = url_validator.validate_python('https://example.com')
    assert isinstance(url, Url)
    assert str(url) == 'https://example.com/'

    url2 = url_validator.validate_python(url)
    assert isinstance(url2, Url)
    assert str(url2) == 'https://example.com/'
    assert url is not url2

    multi_url = multi_host_url_validator.validate_python('https://example.com')
    assert isinstance(multi_url, MultiHostUrl)

    url3 = url_validator.validate_python(multi_url)
    assert isinstance(url3, Url)
    assert str(url3) == 'https://example.com/'

    multi_url2 = multi_host_url_validator.validate_python('foobar://x:y@foo,x:y@bar.com')
    assert isinstance(multi_url2, MultiHostUrl)

    url4 = url_validator.validate_python(multi_url2)
    assert isinstance(url4, Url)
    assert str(url4) == 'foobar://x:y%40foo,x%3Ay@bar.com'
    assert url4.host == 'bar.com'


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
            'type': 'url_scheme',
            'loc': (),
            'msg': "URL scheme should be 'https'",
            'input': IsInstance(Url) & HasRepr("Url('http://example.com/foobar/bar')"),
            'ctx': {'expected_schemes': "'https'"},
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


def test_strict_not_strict(url_validator, strict_url_validator, multi_host_url_validator):
    url = url_validator.validate_python('http:/example.com/foobar/bar')
    assert str(url) == 'http://example.com/foobar/bar'

    url2 = strict_url_validator.validate_python(url)
    assert str(url2) == 'http://example.com/foobar/bar'

    multi_url = multi_host_url_validator.validate_python('https://example.com')
    assert isinstance(multi_url, MultiHostUrl)

    url3 = strict_url_validator.validate_python(multi_url)
    assert isinstance(url3, Url)
    assert str(url3) == 'https://example.com/'

    multi_url2 = multi_host_url_validator.validate_python('foobar://x:y@foo,x:y@bar.com')
    assert isinstance(multi_url2, MultiHostUrl)

    with pytest.raises(ValidationError, match=r'unencoded @ sign in username or password \[type=url_syntax_violation'):
        strict_url_validator.validate_python(multi_url2)


def test_multi_host_url_ok_single(py_and_json: PyAndJson):
    v = py_and_json(core_schema.multi_host_url_schema())
    url: MultiHostUrl = v.validate_test('https://example.com/foo/bar?a=b')
    assert isinstance(url, MultiHostUrl)
    assert str(url) == 'https://example.com/foo/bar?a=b'
    assert repr(url) == "Url('https://example.com/foo/bar?a=b')"
    assert url.scheme == 'https'
    assert url.path == '/foo/bar'
    assert url.query == 'a=b'
    assert url.query_params() == [('a', 'b')]
    assert url.fragment is None
    # insert_assert(url.hosts())
    assert url.hosts() == [{'username': None, 'password': None, 'host': 'example.com', 'port': 443}]

    url: MultiHostUrl = v.validate_test('postgres://foo:bar@example.com:1234')
    assert isinstance(url, MultiHostUrl)
    assert str(url) == 'postgres://foo:bar@example.com:1234'
    assert url.scheme == 'postgres'
    # insert_assert(url.hosts())
    assert url.hosts() == [{'username': 'foo', 'password': 'bar', 'host': 'example.com', 'port': 1234}]


def test_multi_host_url_ok_2(py_and_json: PyAndJson):
    v = py_and_json(core_schema.multi_host_url_schema())
    url: MultiHostUrl = v.validate_test('https://foo.com,bar.com/path')
    assert isinstance(url, MultiHostUrl)
    assert str(url) == 'https://foo.com,bar.com/path'
    assert url.scheme == 'https'
    assert url.path == '/path'
    # insert_assert(url.hosts())
    assert url.hosts() == [
        {'username': None, 'password': None, 'host': 'foo.com', 'port': 443},
        {'username': None, 'password': None, 'host': 'bar.com', 'port': 443},
    ]


@pytest.fixture(scope='module', name='multi_host_url_validator')
def multi_host_url_validator_fixture():
    return SchemaValidator(core_schema.multi_host_url_schema())


@pytest.mark.parametrize(
    'url,expected',
    [
        (
            'http://example.com',
            {
                'str()': 'http://example.com/',
                'hosts()': [{'host': 'example.com', 'password': None, 'port': 80, 'username': None}],
                'unicode_string()': 'http://example.com/',
            },
        ),
        (
            'postgres://example.com',
            {
                'str()': 'postgres://example.com',
                'scheme': 'postgres',
                'hosts()': [{'host': 'example.com', 'password': None, 'port': None, 'username': None}],
            },
        ),
        (
            'mongodb://foo,bar,spam/xxx',
            {
                'str()': 'mongodb://foo,bar,spam/xxx',
                'scheme': 'mongodb',
                'hosts()': [
                    {'host': 'foo', 'password': None, 'port': None, 'username': None},
                    {'host': 'bar', 'password': None, 'port': None, 'username': None},
                    {'host': 'spam', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        ('  mongodb://foo,bar,spam/xxx  ', 'mongodb://foo,bar,spam/xxx'),
        (' \n\r\t mongodb://foo,bar,spam/xxx', 'mongodb://foo,bar,spam/xxx'),
        (
            'mongodb+srv://foo,bar,spam/xxx',
            {
                'str()': 'mongodb+srv://foo,bar,spam/xxx',
                'scheme': 'mongodb+srv',
                'hosts()': [
                    {'host': 'foo', 'password': None, 'port': None, 'username': None},
                    {'host': 'bar', 'password': None, 'port': None, 'username': None},
                    {'host': 'spam', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        (
            'https://foo:bar@example.com,fo%20o:bar@example.com',
            {
                'str()': 'https://foo:bar@example.com,fo%20o:bar@example.com/',
                'scheme': 'https',
                'hosts()': [
                    {'host': 'example.com', 'password': 'bar', 'port': 443, 'username': 'foo'},
                    {'host': 'example.com', 'password': 'bar', 'port': 443, 'username': 'fo%20o'},
                ],
            },
        ),
        (
            'postgres://foo:bar@example.com,fo%20o:bar@example.com',
            {
                'str()': 'postgres://foo:bar@example.com,fo%20o:bar@example.com',
                'scheme': 'postgres',
                'hosts()': [
                    {'host': 'example.com', 'password': 'bar', 'port': None, 'username': 'foo'},
                    {'host': 'example.com', 'password': 'bar', 'port': None, 'username': 'fo%20o'},
                ],
            },
        ),
        ('postgres://', {'str()': 'postgres://', 'scheme': 'postgres', 'hosts()': []}),
        ('postgres://,', Err('empty host')),
        ('postgres://,,', Err('empty host')),
        ('postgres://foo,\n,bar', Err('empty host')),
        ('postgres://\n,bar', Err('empty host')),
        ('postgres://foo,\n', Err('empty host')),
        ('postgres://foo,', Err('empty host')),
        ('postgres://,foo', Err('empty host')),
        ('http://', Err('empty host')),
        ('http://,', Err('empty host')),
        ('http://,,', Err('empty host')),
        ('http://foo,\n,bar', Err('empty host')),
        ('http://\n,bar', Err('empty host')),
        ('http://foo,\n', Err('empty host')),
        ('http://foo,', Err('empty host')),
        ('http://,foo', Err('empty host')),
        ('http@foobar', Err('relative URL without a base')),
        (
            'mongodb://foo\n,b\nar,\nspam/xxx',
            {
                'str()': 'mongodb://foo,bar,spam/xxx',
                'scheme': 'mongodb',
                'hosts()': [
                    {'host': 'foo', 'password': None, 'port': None, 'username': None},
                    {'host': 'bar', 'password': None, 'port': None, 'username': None},
                    {'host': 'spam', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        (
            'postgres://user:pass@host1.db.net:4321,host2.db.net:6432/app',
            {
                'str()': 'postgres://user:pass@host1.db.net:4321,host2.db.net:6432/app',
                'scheme': 'postgres',
                'hosts()': [
                    {'host': 'host1.db.net', 'password': 'pass', 'port': 4321, 'username': 'user'},
                    {'host': 'host2.db.net', 'password': None, 'port': 6432, 'username': None},
                ],
                'path': '/app',
            },
        ),
        (
            'postgresql+py-postgresql://user:pass@localhost:5432/app',
            {
                'str()': 'postgresql+py-postgresql://user:pass@localhost:5432/app',
                'hosts()': [{'host': 'localhost', 'password': 'pass', 'port': 5432, 'username': 'user'}],
            },
        ),
        ('http://foo#bar', 'http://foo/#bar'),
        ('mongodb://foo#bar', 'mongodb://foo#bar'),
        ('http://foo,bar#spam', 'http://foo,bar/#spam'),
        ('mongodb://foo,bar#spam', 'mongodb://foo,bar#spam'),
        ('http://foo,bar?x=y', 'http://foo,bar/?x=y'),
        ('mongodb://foo,bar?x=y', 'mongodb://foo,bar?x=y'),
        ('foo://foo,bar?x=y', 'foo://foo,bar?x=y'),
        (
            (
                'mongodb://mongodb1.example.com:27317,mongodb2.example.com:27017/'
                'mydatabase?replicaSet=mySet&authSource=authDB'
            ),
            {
                'str()': (
                    'mongodb://mongodb1.example.com:27317,mongodb2.example.com:27017/'
                    'mydatabase?replicaSet=mySet&authSource=authDB'
                ),
                'hosts()': [
                    {'host': 'mongodb1.example.com', 'password': None, 'port': 27317, 'username': None},
                    {'host': 'mongodb2.example.com', 'password': None, 'port': 27017, 'username': None},
                ],
                'query_params()': [('replicaSet', 'mySet'), ('authSource', 'authDB')],
            },
        ),
        # with bashslashes
        (
            'FILE:\\\\foo,bar\\more',
            {
                'str()': 'file://foo,bar/more',
                'path': '/more',
                'hosts()': [
                    {'host': 'foo', 'password': None, 'port': None, 'username': None},
                    {'host': 'bar', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        (
            'http:\\\\foo,bar\\more',
            {
                'str()': 'http://foo,bar/more',
                'path': '/more',
                'hosts()': [
                    {'host': 'foo', 'password': None, 'port': 80, 'username': None},
                    {'host': 'bar', 'password': None, 'port': 80, 'username': None},
                ],
            },
        ),
        ('mongo:\\\\foo,bar\\more', Err('empty host')),
        (
            'foobar://foo[]bar:x@y@whatever,foo[]bar:x@y@whichever',
            {
                'str()': 'foobar://foo%5B%5Dbar:x%40y@whatever,foo%5B%5Dbar:x%40y@whichever',
                'hosts()': [
                    {'host': 'whatever', 'password': 'x%40y', 'port': None, 'username': 'foo%5B%5Dbar'},
                    {'host': 'whichever', 'password': 'x%40y', 'port': None, 'username': 'foo%5B%5Dbar'},
                ],
            },
        ),
        (
            'foobar://foo%2Cbar:x@y@whatever,snap',
            {
                'str()': 'foobar://foo%2Cbar:x%40y@whatever,snap',
                'hosts()': [
                    {'host': 'whatever', 'password': 'x%40y', 'port': None, 'username': 'foo%2Cbar'},
                    {'host': 'snap', 'password': None, 'port': None, 'username': None},
                ],
            },
        ),
        (
            'mongodb://x:y@[::1],1.1.1.1:888/xxx',
            {
                'str()': 'mongodb://x:y@[::1],1.1.1.1:888/xxx',
                'scheme': 'mongodb',
                'hosts()': [
                    {'host': '[::1]', 'password': 'y', 'port': None, 'username': 'x'},
                    {'host': '1.1.1.1', 'password': None, 'port': 888, 'username': None},
                ],
            },
        ),
        (
            'http://foo.co.uk,bar.spam.things.com',
            {
                'str()': 'http://foo.co.uk,bar.spam.things.com/',
                'hosts()': [
                    {'host': 'foo.co.uk', 'password': None, 'port': 80, 'username': None},
                    {'host': 'bar.spam.things.com', 'password': None, 'port': 80, 'username': None},
                ],
            },
        ),
        ('ht💣tp://example.com', Err('relative URL without a base')),
        # punycode ß
        (
            'http://£££.com',
            {
                'str()': 'http://xn--9aaa.com/',
                'hosts()': [{'host': 'xn--9aaa.com', 'password': None, 'port': 80, 'username': None}],
                'unicode_string()': 'http://£££.com/',
            },
        ),
        (
            'http://£££.co.uk,münchen.com/foo?bar=baz#qux',
            {
                'str()': 'http://xn--9aaa.co.uk,xn--mnchen-3ya.com/foo?bar=baz#qux',
                'hosts()': [
                    {'host': 'xn--9aaa.co.uk', 'password': None, 'port': 80, 'username': None},
                    {'host': 'xn--mnchen-3ya.com', 'password': None, 'port': 80, 'username': None},
                ],
                'unicode_string()': 'http://£££.co.uk,münchen.com/foo?bar=baz#qux',
            },
        ),
        (
            'postgres://£££.co.uk,münchen.com/foo?bar=baz#qux',
            {
                'str()': 'postgres://%C2%A3%C2%A3%C2%A3.co.uk,m%C3%BCnchen.com/foo?bar=baz#qux',
                'hosts()': [
                    {'host': '%C2%A3%C2%A3%C2%A3.co.uk', 'password': None, 'port': None, 'username': None},
                    {'host': 'm%C3%BCnchen.com', 'password': None, 'port': None, 'username': None},
                ],
                'unicode_string()': 'postgres://%C2%A3%C2%A3%C2%A3.co.uk,m%C3%BCnchen.com/foo?bar=baz#qux',
            },
        ),
    ],
)
def test_multi_url_cases(multi_host_url_validator, url, expected):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            multi_host_url_validator.validate_python(url)
        assert exc_info.value.error_count() == 1
        error = exc_info.value.errors()[0]
        assert error['type'] == 'url_parsing'
        assert error['ctx']['error'] == expected.message
    else:
        output_url = multi_host_url_validator.validate_python(url)
        assert isinstance(output_url, MultiHostUrl)
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
            # debug(output_parts)
            assert output_parts == expected


@pytest.fixture(scope='module', name='strict_multi_host_url_validator')
def strict_multi_host_url_validator_fixture():
    return SchemaValidator(core_schema.multi_host_url_schema(strict=True))


@pytest.mark.parametrize(
    'url,expected',
    [
        ('http://example.com', 'http://example.com/'),
        (
            '  mongodb://foo,bar,spam/xxx  ',
            Err('leading or trailing control or space character are ignored in URLs', 'url_syntax_violation'),
        ),
        (
            ' \n\r\t mongodb://foo,bar,spam/xxx',
            Err('leading or trailing control or space character are ignored in URLs', 'url_syntax_violation'),
        ),
        # with bashslashes
        ('file:\\\\foo,bar\\more', Err('backslash', 'url_syntax_violation')),
        ('http:\\\\foo,bar\\more', Err('backslash', 'url_syntax_violation')),
        ('mongo:\\\\foo,bar\\more', Err('non-URL code point', 'url_syntax_violation')),
        ('foobar://foo[]bar:x@y@whatever,foo[]bar:x@y@whichever', Err('non-URL code point', 'url_syntax_violation')),
        (
            'foobar://foo%2Cbar:x@y@whatever,snap',
            Err('unencoded @ sign in username or password', 'url_syntax_violation'),
        ),
        ('foobar://foo%2Cbar:x%40y@whatever,snap', 'foobar://foo%2Cbar:x%40y@whatever,snap'),
    ],
)
def test_multi_url_cases_strict(strict_multi_host_url_validator, url, expected):
    if isinstance(expected, Err):
        with pytest.raises(ValidationError) as exc_info:
            strict_multi_host_url_validator.validate_python(url)
        assert exc_info.value.error_count() == 1
        error = exc_info.value.errors()[0]
        assert error['type'] == expected.errors
        assert error['ctx']['error'] == expected.message
    else:
        output_url = strict_multi_host_url_validator.validate_python(url)
        assert isinstance(output_url, MultiHostUrl)
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


def test_url_to_multi_url(url_validator, multi_host_url_validator):
    url: Url = url_validator.validate_python('https://example.com')
    assert isinstance(url, Url)
    assert str(url) == 'https://example.com/'

    url2 = multi_host_url_validator.validate_python(url)
    assert isinstance(url2, MultiHostUrl)
    assert str(url2) == 'https://example.com/'
    assert url is not url2

    url3 = multi_host_url_validator.validate_python(url2)
    assert isinstance(url3, MultiHostUrl)
    assert str(url3) == 'https://example.com/'
    assert url2 is not url3


def test_multi_wrong_type(multi_host_url_validator):
    assert str(multi_host_url_validator.validate_python('http://example.com')) == 'http://example.com/'
    with pytest.raises(ValidationError, match=r'URL input should be a string or URL \[type=url_type,'):
        multi_host_url_validator.validate_python(42)


def test_multi_allowed_schemas():
    v = SchemaValidator(core_schema.multi_host_url_schema(allowed_schemes=['http', 'foo']))
    assert str(v.validate_python('http://example.com')) == 'http://example.com/'
    assert str(v.validate_python('foo://example.com')) == 'foo://example.com'
    with pytest.raises(ValidationError, match=r"URL scheme should be 'http' or 'foo' \[type=url_scheme,"):
        v.validate_python('https://example.com')


def test_multi_max_length(url_validator):
    v = SchemaValidator(core_schema.multi_host_url_schema(max_length=25))
    assert str(v.validate_python('http://example.com')) == 'http://example.com/'
    with pytest.raises(ValidationError, match=r'URL should have at most 25 characters \[type=url_too_long,'):
        v.validate_python('https://example.com/this-is-too-long')

    url = v.validate_python('http://example.com')
    assert str(v.validate_python(url)) == 'http://example.com/'

    simple_url = url_validator.validate_python('http://example.com')
    assert isinstance(simple_url, Url)
    assert str(v.validate_python(simple_url)) == 'http://example.com/'

    long_simple_url = url_validator.validate_python('http://example.com/this-is-too-long')
    with pytest.raises(ValidationError, match=r'URL should have at most 25 characters \[type=url_too_long,'):
        v.validate_python(long_simple_url)


def test_zero_schemas():
    with pytest.raises(SchemaError, match='"allowed_schemes" should have length > 0'):
        SchemaValidator(core_schema.multi_host_url_schema(allowed_schemes=[]))


@pytest.mark.parametrize(
    'url,expected',
    [
        # urlparse doesn't follow RFC 3986 Section 3.2
        (
            'http://google.com#@evil.com/',
            dict(
                scheme='http',
                host='google.com',
                # path='', CHANGED
                path='/',
                fragment='@evil.com/',
            ),
        ),
        # CVE-2016-5699
        (
            'http://127.0.0.1%0d%0aConnection%3a%20keep-alive',
            # dict(scheme='http', host='127.0.0.1%0d%0aconnection%3a%20keep-alive'), CHANGED
            Err('Input should be a valid URL, invalid domain character [type=url_parsing,'),
        ),
        # NodeJS unicode -> double dot
        ('http://google.com/\uff2e\uff2e/abc', dict(scheme='http', host='google.com', path='/%EF%BC%AE%EF%BC%AE/abc')),
        # Scheme without ://
        (
            "javascript:a='@google.com:12345/';alert(0)",
            dict(scheme='javascript', path="a='@google.com:12345/';alert(0)"),
        ),
        (
            '//google.com/a/b/c',
            # dict(host='google.com', path='/a/b/c'),
            Err('Input should be a valid URL, relative URL without a base [type=url_parsing,'),
        ),
        # International URLs
        (
            'http://ヒ:キ@ヒ.abc.ニ/ヒ?キ#ワ',
            dict(
                scheme='http',
                host='xn--pdk.abc.xn--idk',
                auth='%E3%83%92:%E3%82%AD',
                path='/%E3%83%92',
                query='%E3%82%AD',
                fragment='%E3%83%AF',
            ),
        ),
        # Injected headers (CVE-2016-5699, CVE-2019-9740, CVE-2019-9947)
        (
            '10.251.0.83:7777?a=1 HTTP/1.1\r\nX-injected: header',
            # dict( CHANGED
            #     host='10.251.0.83',
            #     port=7777,
            #     path='',
            #     query='a=1%20HTTP/1.1%0D%0AX-injected:%20header',
            # ),
            Err('Input should be a valid URL, relative URL without a base [type=url_parsing,'),
        ),
        # ADDED, similar to the above with scheme added
        (
            'http://10.251.0.83:7777?a=1 HTTP/1.1\r\nX-injected: header',
            dict(
                host='10.251.0.83',
                port=7777,
                path='/',
                # query='a=1%20HTTP/1.1%0D%0AX-injected:%20header', CHANGED
                query='a=1%20HTTP/1.1X-injected:%20header',
            ),
        ),
        (
            'http://127.0.0.1:6379?\r\nSET test failure12\r\n:8080/test/?test=a',
            dict(
                scheme='http',
                host='127.0.0.1',
                port=6379,
                # path='',
                path='/',
                # query='%0D%0ASET%20test%20failure12%0D%0A:8080/test/?test=a', CHANGED
                query='SET%20test%20failure12:8080/test/?test=a',
            ),
        ),
        # See https://bugs.xdavidhu.me/google/2020/03/08/the-unexpected-google-wide-domain-check-bypass/
        (
            'https://user:pass@xdavidhu.me\\test.corp.google.com:8080/path/to/something?param=value#hash',
            dict(
                scheme='https',
                auth='user:pass',
                host='xdavidhu.me',
                # path='/%5Ctest.corp.google.com:8080/path/to/something', CHANGED
                path='/test.corp.google.com:8080/path/to/something',
                query='param=value',
                fragment='hash',
            ),
        ),
        # # Tons of '@' causing backtracking
        (
            'https://' + ('@' * 10000) + '[',
            # False, CHANGED
            Err('Input should be a valid URL, invalid IPv6 address [type=url_parsing,'),
        ),
        (
            'https://user:' + ('@' * 10000) + 'example.com',
            dict(scheme='https', auth='user:' + ('%40' * 9999), host='example.com'),
        ),
    ],
)
def test_url_vulnerabilities(url_validator, url, expected):
    """
    Test cases from
    https://github.com/urllib3/urllib3/blob/7ef7444fd0fc22a825be6624af85343cefa36fef/test/test_util.py#L422
    """
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            url_validator.validate_python(url)
    else:
        output_url = url_validator.validate_python(url)
        assert isinstance(output_url, Url)
        output_parts = {}
        for key in expected:
            # one tweak required to match urllib3 logic
            if key == 'auth':
                output_parts[key] = f'{output_url.username}:{output_url.password}'
            else:
                output_parts[key] = getattr(output_url, key)
        assert output_parts == expected
