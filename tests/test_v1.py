import sys
import warnings

import pytest

from pydantic import VERSION
from pydantic import BaseModel as V2BaseModel
from pydantic.v1 import VERSION as V1_VERSION
from pydantic.v1 import BaseModel as V1BaseModel
from pydantic.v1 import BaseSettings as V1BaseSettings
from pydantic.v1 import root_validator as v1_root_validator


def test_version():
    assert V1_VERSION.startswith('1.')
    assert V1_VERSION != VERSION


@pytest.mark.skipif(sys.version_info >= (3, 14), reason='Python 3.14+ not supported')
@pytest.mark.thread_unsafe(reason='Mutates the value')
def test_root_validator():
    class Model(V1BaseModel):
        v: str

        @v1_root_validator(pre=True)
        @classmethod
        def root_validator(cls, values):
            values['v'] += '-v1'
            return values

    model = Model(v='value')
    assert model.v == 'value-v1'


def test_isinstance_does_not_raise_deprecation_warnings():
    class V1Model(V1BaseModel):
        v: int

    class V2Model(V2BaseModel):
        v: int

    v1_obj = V1Model(v=1)
    v2_obj = V2Model(v=2)

    with warnings.catch_warnings():
        warnings.simplefilter('error')

        assert isinstance(v1_obj, V1BaseModel)
        assert not isinstance(v1_obj, V2BaseModel)
        assert not isinstance(v2_obj, V1BaseModel)
        assert isinstance(v2_obj, V2BaseModel)


def test_v1_base_settings_legacy_build_values_signature(tmp_path):
    """Subclasses that override `_build_values` without newer kwargs must not break `__init__`."""

    class Settings(V1BaseSettings):
        foo: str = 'default'

        class Config:
            secrets_dir = tmp_path

        def _build_values(self, init_kwargs, _env_file=None, _env_file_encoding=None):
            return super()._build_values(init_kwargs, _env_file=_env_file, _env_file_encoding=_env_file_encoding)

    (tmp_path / 'foo').write_text('from-secret', encoding='utf-8')
    assert Settings().foo == 'from-secret'


def test_v1_secrets_file_utf8(tmp_path):
    class Settings(V1BaseSettings):
        token: str

        class Config:
            secrets_dir = tmp_path

    (tmp_path / 'token').write_text('\u03bb', encoding='utf-8')
    assert Settings().token == '\u03bb'
