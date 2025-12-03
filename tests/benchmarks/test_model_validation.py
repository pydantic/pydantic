from typing import Any, Callable

import pytest

from pydantic import BaseModel

from .shared import ComplexModel, OuterModel, SimpleModel

pytestmark = [
    pytest.mark.benchmark(group="model_validation"),
    pytest.mark.parametrize("method", ["model_validate", "__init__"]),
]


class SimpleListModel(BaseModel):
    items: list[SimpleModel]


def _get_validator(
    model: type[BaseModel], method: str
) -> Callable[[dict[str, Any]], BaseModel]:
    if method == "__init__":
        return lambda data: model(**data)
    return model.model_validate


@pytest.fixture
def simple_model_data() -> dict[str, Any]:
    return {"field1": "test", "field2": 42, "field3": 3.14}


@pytest.fixture
def nested_model_data() -> dict[str, Any]:
    return {
        "nested": {
            "field1": "test",
            "field2": [1, 2, 3],
            "field3": {"a": 1.1, "b": 2.2},
        },
        "optional_nested": None,
    }


@pytest.fixture
def complex_model_data() -> dict[str, Any]:
    return {
        "field1": "test",
        "field2": [{"a": 1, "b": 2.2}, {"c": 3, "d": 4.4}],
        "field3": ["test", 1, 2, "test2"],
    }


@pytest.fixture
def list_model_data() -> dict[str, Any]:
    return {
        "items": [
            {"field1": f"test{i}", "field2": i, "field3": float(i)} for i in range(10)
        ]
    }


def test_simple_model_validation(
    method: str, benchmark, simple_model_data: dict[str, Any]
):
    validator = _get_validator(SimpleModel, method)
    benchmark(validator, simple_model_data)


def test_nested_model_validation(
    method: str, benchmark, nested_model_data: dict[str, Any]
):
    validator = _get_validator(OuterModel, method)
    benchmark(validator, nested_model_data)


def test_complex_model_validation(
    method: str, benchmark, complex_model_data: dict[str, Any]
):
    validator = _get_validator(ComplexModel, method)
    benchmark(validator, complex_model_data)


def test_list_of_models_validation(
    method: str, benchmark, list_model_data: dict[str, Any]
):
    validator = _get_validator(SimpleListModel, method)
    benchmark(validator, list_model_data)
