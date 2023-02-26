import pytest

from pydantic.import_helper import V2MigrationRemoved


def test_import_helper_removed():
    with pytest.raises(V2MigrationRemoved):
        from pydantic import Required  # noqa: F401
