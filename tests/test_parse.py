import pickle

import pytest

from pydantic import BaseModel, Protocol, ValidationError


class Model(BaseModel):
    a: float = ...
    b: int = 10


def test_obj():
    m = Model.parse_obj(dict(a=10.2))
    assert str(m) == 'Model a=10.2 b=10'


def test_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj([1, 2, 3])
    assert exc_info.value.errors() == [
        {'loc': ('__obj__',), 'msg': 'Model expected dict not list', 'type': 'type_error'}
    ]


def test_json():
    assert Model.parse_raw('{"a": 12, "b": 8}') == Model(a=12, b=8)


def test_json_ct():
    assert Model.parse_raw('{"a": 12, "b": 8}', content_type='application/json') == Model(a=12, b=8)


def test_pickle_ct():
    data = pickle.dumps(dict(a=12, b=8))
    assert Model.parse_raw(data, content_type='application/pickle', allow_pickle=True) == Model(a=12, b=8)


def test_pickle_proto():
    data = pickle.dumps(dict(a=12, b=8))
    assert Model.parse_raw(data, proto=Protocol.pickle, allow_pickle=True) == Model(a=12, b=8)


def test_pickle_not_allowed():
    data = pickle.dumps(dict(a=12, b=8))
    with pytest.raises(RuntimeError):
        Model.parse_raw(data, proto=Protocol.pickle)


def test_bad_ct():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', content_type='application/missing')
    assert exc_info.value.errors() == [
        {'loc': ('__obj__',), 'msg': 'Unknown content-type: application/missing', 'type': 'type_error'}
    ]


def test_bad_proto():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_raw('{"a": 12, "b": 8}', proto='foobar')
    assert exc_info.value.errors() == [{'loc': ('__obj__',), 'msg': 'Unknown protocol: foobar', 'type': 'type_error'}]


def test_file_json(tmpdir):
    p = tmpdir.join('test.json')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model(a=12, b=8)


def test_file_json_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write('{"a": 12, "b": 8}')
    assert Model.parse_file(str(p)) == Model(a=12, b=8)


def test_file_pickle(tmpdir):
    p = tmpdir.join('test.pkl')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), allow_pickle=True) == Model(a=12, b=8)


def test_file_pickle_no_ext(tmpdir):
    p = tmpdir.join('test')
    p.write_binary(pickle.dumps(dict(a=12, b=8)))
    assert Model.parse_file(str(p), content_type='application/pickle', allow_pickle=True) == Model(a=12, b=8)
