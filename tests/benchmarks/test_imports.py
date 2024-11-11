import pytest


@pytest.mark.benchmark
def test_import_basemodel(benchmark) -> None:
    @benchmark
    def run():
        from pydantic import BaseModel

        assert BaseModel


@pytest.mark.benchmark
def test_import_field(benchmark) -> None:
    @benchmark
    def run():
        from pydantic import Field

        assert Field
