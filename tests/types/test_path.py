import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    NewPath,
    SocketPath,
    TypeAdapter,
    ValidationError,
)


def test_path_default():
    """Regression test for https://github.com/pydantic/pydantic/issues/13318."""

    class Config(BaseModel):
        path: Path = Path('config.toml')

    assert Config.model_json_schema()['properties']['path']['default'] == 'config.toml'


@pytest.mark.parametrize('value,result', (('/test/path', Path('/test/path')), (Path('/test/path'), Path('/test/path'))))
def test_path_validation_success(value, result):
    ta = TypeAdapter(Path)

    assert ta.validate_python(value) == result
    assert ta.validate_json(json.dumps(str(value))) == result


def test_path_like():
    class Model(BaseModel):
        foo: os.PathLike

    assert Model(foo='/foo/bar').foo == Path('/foo/bar')
    assert Model(foo=Path('/foo/bar')).foo == Path('/foo/bar')
    assert Model.model_validate_json('{"foo": "abc"}').foo == Path('abc')
    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {'foo': {'type': 'string', 'format': 'path', 'title': 'Foo'}},
        'required': ['foo'],
        'title': 'Model',
    }


def test_path_like_extra_subtype():
    class Model(BaseModel):
        str_type: os.PathLike[str]
        byte_type: os.PathLike[bytes]
        any_type: os.PathLike[Any]

    m = Model(
        str_type='/foo/bar',
        byte_type=b'/foo/bar',
        any_type='/foo/bar',
    )
    assert m.str_type == Path('/foo/bar')
    assert m.byte_type == Path('/foo/bar')
    assert m.any_type == Path('/foo/bar')
    assert Model.model_json_schema() == {
        'properties': {
            'str_type': {'format': 'path', 'title': 'Str Type', 'type': 'string'},
            'byte_type': {'format': 'path', 'title': 'Byte Type', 'type': 'string'},
            'any_type': {'format': 'path', 'title': 'Any Type', 'type': 'string'},
        },
        'required': ['str_type', 'byte_type', 'any_type'],
        'title': 'Model',
        'type': 'object',
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(
            str_type=b'/foo/bar',
            byte_type='/foo/bar',
            any_type=111,
        )
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_type',
            'loc': ('str_type',),
            'msg': "Input is not a valid path for <class 'os.PathLike'>",
            'input': b'/foo/bar',
        },
        {
            'type': 'path_type',
            'loc': ('byte_type',),
            'msg': "Input is not a valid path for <class 'os.PathLike'>",
            'input': '/foo/bar',
        },
        {
            'type': 'path_type',
            'loc': ('any_type',),
            'msg': "Input is not a valid path for <class 'os.PathLike'>",
            'input': 111,
        },
    ]


def test_path_like_strict():
    class Model(BaseModel):
        model_config = dict(strict=True)

        foo: os.PathLike

    with pytest.raises(ValidationError, match='Input should be an instance of PathLike'):
        Model(foo='/foo/bar')
    assert Model(foo=Path('/foo/bar')).foo == Path('/foo/bar')
    assert Model.model_validate_json('{"foo": "abc"}').foo == Path('abc')
    # insert_assert(Model.model_json_schema())
    assert Model.model_json_schema() == {
        'type': 'object',
        'properties': {'foo': {'type': 'string', 'format': 'path', 'title': 'Foo'}},
        'required': ['foo'],
        'title': 'Model',
    }


def test_path_strict_override():
    class Model(BaseModel):
        model_config = ConfigDict(strict=True)

        x: Path = Field(strict=False)

    m = Model(x='/foo/bar')
    assert m.x == Path('/foo/bar')


def test_path_validation_fails():
    ta = TypeAdapter(Path)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(123)
    # insert_assert(exc_info.value.errors(include_url=False))[0]['type']
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'path_type'

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(None)
    # insert_assert(exc_info.value.errors(include_url=False))[0]['type']
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'path_type'


def test_path_validation_strict():
    ta = TypeAdapter(Path)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('/test/path', strict=True)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of Path',
            'input': '/test/path',
            'ctx': {'class': 'Path'},
        }
    ]

    assert ta.validate_python(Path('/test/path'), strict=True) == Path('/test/path')


@pytest.mark.parametrize(
    'value,result',
    (('tests/test_types.py', Path('tests/test_types.py')), (Path('tests/test_types.py'), Path('tests/test_types.py'))),
)
def test_file_path_validation_success(value, result):
    ta = TypeAdapter(FilePath)

    assert ta.validate_python(value) == result


@pytest.mark.parametrize('value', ['nonexistentfile', Path('nonexistentfile'), 'tests', Path('tests')])
def test_file_path_validation_fails(value):
    ta = TypeAdapter(FilePath)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_not_file',
            'loc': (),
            'msg': 'Path does not point to a file',
            'input': value,
        }
    ]


@pytest.mark.parametrize('value,result', (('tests', Path('tests')), (Path('tests'), Path('tests'))))
def test_directory_path_validation_success(value, result):
    ta = TypeAdapter(DirectoryPath)

    assert ta.validate_python(value) == result


@pytest.mark.parametrize(
    'value', ['nonexistentdirectory', Path('nonexistentdirectory'), 'tests/test_t.py', Path('tests/test_ypestypes.py')]
)
def test_directory_path_validation_fails(value):
    ta = TypeAdapter(DirectoryPath)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_not_directory',
            'loc': (),
            'msg': 'Path does not point to a directory',
            'input': value,
        }
    ]


@pytest.mark.parametrize('value', ('tests/test_types.py', Path('tests/test_types.py')))
def test_new_path_validation_path_already_exists(value):
    ta = TypeAdapter(NewPath)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_exists',
            'loc': (),
            'msg': 'Path already exists',
            'input': value,
        }
    ]


@pytest.mark.skipif(
    not sys.platform.startswith('linux'),
    reason='Test only works for linux systems. Windows excluded (unsupported). Mac excluded due to CI issues.',
)
def test_socket_exists(tmp_path):
    import socket

    # Working around path length limits by reducing character count where possible.
    target = tmp_path / 's'
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.bind(str(target))

        ta = TypeAdapter(SocketPath)

        assert ta.validate_python(target) == target


def test_socket_not_exists(tmp_path):
    target = tmp_path / 's'

    ta = TypeAdapter(SocketPath)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(target)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'path_not_socket',
            'loc': (),
            'msg': 'Path does not point to a socket',
            'input': target,
        }
    ]


@pytest.mark.parametrize('value', ('/nonexistentdir/foo.py', Path('/nonexistentdir/foo.py')))
def test_new_path_validation_parent_does_not_exist(value):
    ta = TypeAdapter(NewPath)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'parent_does_not_exist',
            'loc': (),
            'msg': 'Parent directory does not exist',
            'input': value,
        }
    ]


@pytest.mark.parametrize(
    'value,result', (('tests/foo.py', Path('tests/foo.py')), (Path('tests/foo.py'), Path('tests/foo.py')))
)
def test_new_path_validation_success(value, result):
    ta = TypeAdapter(NewPath)

    assert ta.validate_python(value) == result


def test_path_union_ser() -> None:
    class Model(BaseModel):
        a: Path | list[Path]
        b: list[Path] | Path

    model = Model(a=Path('potato'), b=Path('potato'))
    assert model.model_dump() == {'a': Path('potato'), 'b': Path('potato')}
    assert model.model_dump_json() == '{"a":"potato","b":"potato"}'

    model = Model(a=[Path('potato')], b=[Path('potato')])
    assert model.model_dump() == {'a': [Path('potato')], 'b': [Path('potato')]}
    assert model.model_dump_json() == '{"a":["potato"],"b":["potato"]}'


def test_ser_path_incorrect() -> None:
    ta = TypeAdapter(Path)
    with pytest.warns(UserWarning, match='serialized value may not be as expected.'):
        ta.dump_python(123)
