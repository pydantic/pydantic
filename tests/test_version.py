from unittest.mock import patch

import pytest
from packaging.version import parse as parse_version

import pydantic
from pydantic.version import version_info, version_short


def test_version_info():
    version_info_fields = [
        'pydantic version',
        'pydantic-core version',
        'pydantic-core build',
        'install path',
        'python version',
        'platform',
        'related packages',
        'commit',
    ]

    s = version_info()
    assert all([f'{field}:' in s for field in version_info_fields])
    assert s.count('\n') == 7


def test_standard_version():
    v = parse_version(pydantic.VERSION)
    assert str(v) == pydantic.VERSION


def test_version_attribute_is_present():
    assert hasattr(pydantic, '__version__')


def test_version_attribute_is_a_string():
    assert isinstance(pydantic.__version__, str)


@pytest.mark.parametrize('version,expected', (('2.1', '2.1'), ('2.1.0', '2.1')))
def test_version_short(version, expected):
    with patch('pydantic.version.VERSION', version):
        assert version_short() == expected
