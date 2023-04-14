import re

from packaging.version import parse as parse_version

import pydantic
from pydantic.version import version_info


def test_version_info():
    s = version_info()
    assert re.match(' *pydantic version: ', s)
    assert s.count('\n') == 5


def test_standard_version():
    v = parse_version(pydantic.VERSION)
    assert str(v) == pydantic.VERSION


def test_version_attribute_is_present():
    assert hasattr(pydantic, '__version__')


def test_version_attribute_is_a_string():
    assert isinstance(pydantic.__version__, str)
