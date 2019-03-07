import pytest

from pydantic import BaseModel, ValidationError, urlstr


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'https://example.org',
        'ftp://example.org',
        'ftps://example.org',
        'http://example.co.jp',
        'http://www.example.com/a%C2%B1b',
        'http://www.example.com/~username/',
        'http://info.example.com/?fred',
        'http://xn--mgbh0fb.xn--kgbechtv/',
        'http://example.com/blue/red%3Fand+green',
        'http://www.example.com/?array%5Bkey%5D=value',
        'http://xn--rsum-bpad.example.org/',
        'http://123.45.67.8/',
        'http://123.45.67.8:8329/',
        'http://[2001:db8::ff00:42]:8329',
        'http://[2001::1]:8329',
        'http://www.example.com:8000/foo',
    ],
)
def test_url_str_absolute_success(value):
    class Model(BaseModel):
        v: urlstr(relative=False)

    assert Model(v=value).v == value


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'http:///example.com/',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'https:///example.com/',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'https://example.org\\',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'ftp:///example.com/',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'ftps:///example.com/',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'http//example.org',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        ('http:///', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        (
            'http:/example.org',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'foo://example.org',
            [
                {
                    'loc': ('v',),
                    'msg': 'url scheme "foo" is not allowed',
                    'type': 'value_error.url.scheme',
                    'ctx': {'scheme': 'foo'},
                }
            ],
        ),
        (
            '../icons/logo.gif',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'http://2001:db8::ff00:42:8329',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'http://[192.168.1.1]:8329',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        ('abc', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        ('..', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        ('/', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        (
            ' ',
            [
                {
                    'loc': ('v',),
                    'msg': 'ensure this value has at least 1 characters',
                    'type': 'value_error.any_str.min_length',
                    'ctx': {'limit_value': 1},
                }
            ],
        ),
        (
            '',
            [
                {
                    'loc': ('v',),
                    'msg': 'ensure this value has at least 1 characters',
                    'type': 'value_error.any_str.min_length',
                    'ctx': {'limit_value': 1},
                }
            ],
        ),
        (None, [{'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}]),
    ],
)
def test_url_str_absolute_fails(value, errors):
    class Model(BaseModel):
        v: urlstr(relative=False)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'http://123.45.67.8/',
        'http://example.com/foo/bar/../baz',
        'https://example.com/../icons/logo.gif',
        'http://example.com/./icons/logo.gif',
        'ftp://example.com/../../../../g',
        'http://example.com/g?y/./x',
    ],
)
def test_url_str_relative_success(value):
    class Model(BaseModel):
        v: urlstr(relative=True)

    assert Model(v=value).v == value


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            'http//example.org',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'suppliers.html',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            '../icons/logo.gif',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            '\\icons/logo.gif',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        ('../.../g', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        ('...', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        ('\\', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        (
            ' ',
            [
                {
                    'loc': ('v',),
                    'msg': 'ensure this value has at least 1 characters',
                    'type': 'value_error.any_str.min_length',
                    'ctx': {'limit_value': 1},
                }
            ],
        ),
        (
            '',
            [
                {
                    'loc': ('v',),
                    'msg': 'ensure this value has at least 1 characters',
                    'type': 'value_error.any_str.min_length',
                    'ctx': {'limit_value': 1},
                }
            ],
        ),
        (None, [{'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}]),
    ],
)
def test_url_str_relative_fails(value, errors):
    class Model(BaseModel):
        v: urlstr(relative=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize(
    'value',
    [
        'http://example.org',
        'http://123.45.67.8/',
        'http://example',
        'http://example.',
        'http://example:80',
        'http://user.name:pass.word@example',
        'http://example/foo/bar',
    ],
)
def test_url_str_dont_require_tld_success(value):
    class Model(BaseModel):
        v: urlstr(require_tld=False)

    assert Model(v=value).v == value


@pytest.mark.parametrize(
    'value,errors',
    [
        ('http//example', [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}]),
        (
            'http://.example.org',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'http:///foo/bar',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            'http:// /foo/bar',
            [{'loc': ('v',), 'msg': 'url string does not match regex', 'type': 'value_error.url.regex'}],
        ),
        (
            '',
            [
                {
                    'loc': ('v',),
                    'msg': 'ensure this value has at least 1 characters',
                    'type': 'value_error.any_str.min_length',
                    'ctx': {'limit_value': 1},
                }
            ],
        ),
        (None, [{'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}]),
    ],
)
def test_url_str_dont_require_tld_fails(value, errors):
    class Model(BaseModel):
        v: urlstr(require_tld=False)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


def test_url_str_absolute_custom_scheme():
    class Model(BaseModel):
        v: urlstr(relative=False)

    # By default, ws not allowed
    url = 'ws://test.test'
    with pytest.raises(ValidationError) as exc_info:
        Model(v=url)
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'url scheme "ws" is not allowed',
            'type': 'value_error.url.scheme',
            'ctx': {'scheme': 'ws'},
        }
    ]

    class Model(BaseModel):
        v: urlstr(relative=False, schemes={'http', 'https', 'ws'})

    assert Model(v=url).v == url


def test_url_str_relative_and_custom_schemes():
    class Model(BaseModel):
        v: urlstr(relative=True)

    # By default, ws not allowed
    url = 'ws://test.test'
    with pytest.raises(ValidationError) as exc_info:
        Model(v=url)
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'url scheme "ws" is not allowed',
            'type': 'value_error.url.scheme',
            'ctx': {'scheme': 'ws'},
        }
    ]

    class Model(BaseModel):
        v: urlstr(relative=True, schemes={'http', 'https', 'ws'})

    assert Model(v=url).v == url
