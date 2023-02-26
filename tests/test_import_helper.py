from importlib import import_module

import pytest

from pydantic.import_helper import V2MigrationMovedWarning, V2MigrationRemovedException


def import_from(object_import: str):
    module, obj_name = object_import.rsplit('.', 1)
    module = import_module(module)
    return getattr(module, obj_name)


expected_exception = pytest.raises(V2MigrationRemovedException)
expected_warning = pytest.warns(
    V2MigrationMovedWarning,
    match='ValidationError has been moved from pydantic.error_wrappers during the migration to V2\n'
    'Please use either:\n'
    'from pydantic import ValidationError\n'
    'or\n'
    'from pydantic_core import ValidationError',
)


def test_import_helper_raises_removed():
    with expected_exception:
        from pydantic import Required  # noqa: F401


def test_import_helper_raises_removed_getattr():
    with expected_exception:
        import pydantic

        pydantic.Required


def test_import_helper_raises_removed_importlib():
    with expected_exception:
        pydantic = import_module('pydantic')
        pydantic.Required


def test_import_helper_raises_removed_import_from():
    with expected_exception:
        pydantic = import_from('pydantic.Required')  # noqa: F841


def test_import_helper_raises_removed__import__():
    with expected_exception:
        pydantic = __import__('pydantic')
        pydantic.Required


def test_import_helper_warns_and_returns_moved():
    with expected_warning:
        from pydantic.error_wrappers import ValidationError  # noqa: F401


def test_import_helper_warns_and_returns_moved_getattr():
    with expected_warning:
        import pydantic.error_wrappers

        pydantic.error_wrappers.ValidationError


def test_import_helper_warns_and_returns_moved_importlib():
    with expected_warning:
        pydantic = import_module('pydantic')
        pydantic.error_wrappers.ValidationError


def test_import_helper_warns_and_returns_moved_import_from():
    with expected_warning:
        pydantic = import_from('pydantic.error_wrappers.ValidationError')  # noqa: F841


def test_import_helper_warns_and_returns_moved__import__():
    with expected_warning:
        pydantic = __import__('pydantic')
        pydantic.error_wrappers.ValidationError
