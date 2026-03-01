from unittest.mock import patch

import pytest
from packaging.version import parse as parse_version

import pydantic
from pydantic.version import check_pydantic_core_version, parse_mypy_version, version_info, version_short


def test_version_info():
    version_info_fields = [
        'pydantic version',
        'pydantic-core version',
        'pydantic-core build',
        'python version',
        'platform',
        'related packages',
        'commit',
    ]

    s = version_info()
    assert all(f'{field}:' in s for field in version_info_fields)
    assert s.count('\n') == 6


def test_standard_version():
    v = parse_version(pydantic.VERSION)
    assert str(v) == pydantic.VERSION


def test_version_attribute_is_present():
    assert hasattr(pydantic, '__version__')


def test_version_attribute_is_a_string():
    assert isinstance(pydantic.__version__, str)


def test_check_pydantic_core_version() -> None:
    assert check_pydantic_core_version()


@pytest.mark.thread_unsafe(reason='Monkeypatching')
@pytest.mark.parametrize('version,expected', (('2.1', '2.1'), ('2.1.0', '2.1')))
def test_version_short(version, expected):
    with patch('pydantic.version.VERSION', version):
        assert version_short() == expected


@pytest.mark.parametrize(
    'version,expected',
    [
        ('1.11.0', (1, 11, 0)),
        ('1.0.0', (1, 0, 0)),
        ('2.5.1', (2, 5, 1)),
        ('1.11.0+dev.d6d9d8cd4f27c52edac1f537e236ec48a01e54cb.dirty', (1, 11, 0)),
        ('1.0.0+something', (1, 0, 0)),
    ],
)
def test_parse_mypy_version(version: str, expected: tuple[int, int, int]) -> None:
    """Test that mypy version strings are correctly parsed to 3-tuples of ints."""
    assert parse_mypy_version(version) == expected
