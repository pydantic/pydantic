import pytest

from pydantic_core import MultiHostUrl, SchemaSerializer, SchemaValidator, Url, core_schema


def test_url():
    v = SchemaValidator(core_schema.url_schema())
    s = SchemaSerializer(core_schema.url_schema())

    url = v.validate_python('https://example.com')
    assert isinstance(url, Url)
    assert str(url) == 'https://example.com/'
    assert url.host == 'example.com'

    assert s.to_python(url) == url
    assert s.to_python(url, mode='json') == 'https://example.com/'
    assert s.to_json(url) == b'"https://example.com/"'

    with pytest.warns(UserWarning, match='Expected `url` but got `str` - serialized value may not be as expected'):
        assert s.to_python('https://example.com', mode='json') == 'https://example.com'


def test_multi_host_url():
    v = SchemaValidator(core_schema.multi_host_url_schema())
    s = SchemaSerializer(core_schema.multi_host_url_schema())

    url = v.validate_python('https://example.com,example.org/path')
    assert isinstance(url, MultiHostUrl)
    assert str(url) == 'https://example.com,example.org/path'
    assert [h['host'] for h in url.hosts()] == ['example.com', 'example.org']

    assert s.to_python(url) == url
    assert s.to_python(url, mode='json') == 'https://example.com,example.org/path'
    assert s.to_json(url) == b'"https://example.com,example.org/path"'

    with pytest.warns(
        UserWarning, match='Expected `multi-host-url` but got `str` - serialized value may not be as expected'
    ):
        assert s.to_python('https://ex.com,ex.org/path', mode='json') == 'https://ex.com,ex.org/path'


def test_url_dict_keys():
    v = SchemaValidator(core_schema.url_schema())

    s = SchemaSerializer(core_schema.dict_schema(core_schema.url_schema()))
    url = v.validate_python('https://example.com')
    assert s.to_python({url: 'foo'}) == {url: 'foo'}
    assert s.to_python({url: 'foo'}, mode='json') == {'https://example.com/': 'foo'}
    assert s.to_json({url: 'foo'}) == b'{"https://example.com/":"foo"}'


def test_multi_host_url_dict_keys():
    v = SchemaValidator(core_schema.multi_host_url_schema())

    s = SchemaSerializer(core_schema.dict_schema(core_schema.multi_host_url_schema()))
    url = v.validate_python('https://example.com,example.org/path')
    assert s.to_python({url: 'foo'}) == {url: 'foo'}
    assert s.to_python({url: 'foo'}, mode='json') == {'https://example.com,example.org/path': 'foo'}
    assert s.to_json({url: 'foo'}) == b'{"https://example.com,example.org/path":"foo"}'


def test_any():
    url = Url('https://ex.com')
    multi_host_url = MultiHostUrl('https://ex.com,ex.org/path')

    s = SchemaSerializer(core_schema.any_schema())
    assert s.to_python(url) == url
    assert type(s.to_python(url)) == Url
    assert s.to_python(multi_host_url) == multi_host_url
    assert type(s.to_python(multi_host_url)) == MultiHostUrl
    assert s.to_python(url, mode='json') == 'https://ex.com/'
    assert s.to_python(multi_host_url, mode='json') == 'https://ex.com,ex.org/path'
    assert s.to_json(url) == b'"https://ex.com/"'
    assert s.to_json(multi_host_url) == b'"https://ex.com,ex.org/path"'

    assert s.to_python({url: 1, multi_host_url: 2}) == {url: 1, multi_host_url: 2}
    assert s.to_python({url: 1, multi_host_url: 2}, mode='json') == {
        'https://ex.com/': 1,
        'https://ex.com,ex.org/path': 2,
    }
    assert s.to_json({url: 1, multi_host_url: 2}) == b'{"https://ex.com/":1,"https://ex.com,ex.org/path":2}'


def test_custom_serializer():
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.simple_ser_schema('multi-host-url')))

    multi_host_url = MultiHostUrl('https://ex.com,ex.org/path')
    assert s.to_python(multi_host_url) == multi_host_url
