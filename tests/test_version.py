import pydantic


def test_version_attribute_is_present():
    assert hasattr(pydantic, '__version__')


def test_version_attribute_is_a_string():
    assert isinstance(pydantic.__version__, str)
