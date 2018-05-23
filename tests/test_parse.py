import pickle

import pytest

from pydantic import BaseModel, Protocol, ValidationError

try:
    import msgpack
except ImportError:
    msgpack = None


class Model(BaseModel):
    a: float = ...
    b: int = 10


def test_obj():
    m = Model.parse_obj(dict(a=10.2))
    assert str(m) == 'Model a=10.2 b=10'


def test_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj([1, 2, 3])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('__obj__',),
            'msg': 'Model expected dict not list',
            'type': 'type_error',
        },
    ]


def test_json():
    assert Model.parse_raw('{"a": 12, "b": 8}') == Model.construct(a=12, b=8)


def test_json_ct():
    assert Model.parse_raw('{"a": 12, "b": 8}', content_type='application/json') == Model.construct(a=12, b=8)


@pytest.mark.skipif(not msgpack, reason='msgpack not installed')
def test_msgpack_proto(mocker):
    # b'\x82\xa1a\x0c\xa1b\x08' == msgpack.packb(dict(a=12, b=8))
    assert Model.parse_raw(b'\x82\xa1a\x0c\xa1b\x08', proto=Protocol.msgpack) == Model.construct(a=12, b=8)


@pytest.mark.skipif(not msgpack, reason='msgpack not installed')
def test_msgpack_ct():
    assert Model.parse_raw(b'\x82\xa1a\x0c\xa1b\x08', content_type='application/msgpack') == Model.construct(a=12, b=8)


@pytest.mark.skipif(msgpack, reason='msgpack installed')
def test_msgpack_not_installed_proto(mocker):
    with pytest.raises(ImportError) as exc_info:
        Model.parse_raw(b'\x82\xa1a\x0c\xa1b\x08', proto=Protocol.msgpack)
    assert "ImportError: msgpack not installed, can't parse data" in str(exc_info)


@pytest.mark.skipif(msgpack, reason='msgpack installed')
def test_msgpack_not_installed_ct():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw(b'\x82\xa1a\x0c\xa1b\x08', content_type='application/msgpack')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('__obj__',),
            'msg': 'Unknown content-type: application/msgpack',
            'type': 'type_error',
        },
    ]


def test_pickle_ct():
    data = pickle.dumps(dict(a=12, b=8))
    assert Model.parse_raw(data, content_type='application/pickle', allow_pickle=True) == Model.construct(a=12, b=8)


def test_pickle_proto():
    data = pickle.dumps(dict(a=12, b=8))
    assert Model.parse_raw(data, proto=Protocol.pickle, allow_pickle=True) == Model.construct(a=12, b=8)


def test_pickle_not_allowed():
    data = pickle.dumps(dict(a=12, b=8))
    with pytest.raises(RuntimeError):
        Model.parse_raw(data, proto=Protocol.pickle)


def test_bad_ct():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', content_type='application/missing')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('__obj__',),
            'msg': 'Unknown content-type: application/missing',
            'type': 'type_error',
        },
    ]


def test_bad_proto():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', proto='foobar')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('__obj__',),
            'msg': 'Unknown protocol: foobar',
            'type': 'type_error',
        },
    ]


def test_file_json(tmpdir):
    p = tmpdir.join('test.json')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model.construct(a=12, b=8)


def test_file_json_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model.construct(a=12, b=8)


@pytest.mark.skipif(not msgpack, reason='msgpack not installed')
def test_file_msgpack(tmpdir):
    p = tmpdir.join('test.mp')
    p.write_binary(b'\x82\xa1a\x0c\xa1b\x08')
    assert Model.parse_file(str(p)) == Model.construct(a=12, b=8)


def test_file_pickle(tmpdir):
    p = tmpdir.join('test.pkl')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), allow_pickle=True) == Model.construct(a=12, b=8)


def test_file_pickle_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), content_type='application/pickle', allow_pickle=True) == Model.construct(a=12, b=8)
