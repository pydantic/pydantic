import pytest


@pytest.mark.benchmark
def test_import_basemodel() -> None:
    from pydantic import BaseModel

    assert BaseModel


@pytest.mark.benchmark
def test_import_field() -> None:
    from pydantic import Field

    assert Field
