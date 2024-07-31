import pytest


@pytest.mark.benchmark
def import_basemodel() -> None:
    pass


@pytest.mark.benchmark
def import_field() -> None:
    pass
