"""https://github.com/pydantic/pydantic/issues/6768"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, List, TypeVar

from typing_extensions import Annotated

from pydantic import BaseModel, TypeAdapter, create_model
from pydantic.fields import FieldInfo

TYPES_DEFAULTS = {int: 0, str: '', bool: False}  # some dummy basic types with defaults for some fields
TYPES = [*TYPES_DEFAULTS.keys()]
# these are set low to minimise test time, they're increased below in the cProfile call
INNER_DATA_MODEL_COUNT = 5
OUTER_DATA_MODEL_COUNT = 5


def create_data_models() -> list[Any]:
    # Create varying inner models with different sizes and fields (not actually realistic)
    models = []
    for i in range(INNER_DATA_MODEL_COUNT):
        fields = {}
        for j in range(i):
            type_ = TYPES[j % len(TYPES)]
            type_default = TYPES_DEFAULTS[type_]
            if j % 4 == 0:
                type_ = List[type_]
                type_default = []

            default = ... if j % 2 == 0 else type_default
            fields[f'f{j}'] = (type_, default)
        models.append(create_model(f'M1{i}', **fields))

    # Crate varying outer models where some fields use the inner models (not really realistic)
    models_with_nested = []
    for i in range(OUTER_DATA_MODEL_COUNT):
        fields = {}
        for j in range(i):
            type_ = models[j % len(models)] if j % 2 == 0 else TYPES[j % len(TYPES)]
            if j % 4 == 0:
                type_ = List[type_]
            fields[f'f{j}'] = (type_, ...)
        models_with_nested.append(create_model(f'M2{i}', **fields))

    return [*models, *models_with_nested]


def test_fastapi_startup_perf(benchmark: Any):
    data_models = create_data_models()
    # API models for reading / writing the different data models
    T = TypeVar('T')

    class GetModel(BaseModel, Generic[T]):
        res: T

    class GetModel2(GetModel[T], Generic[T]):
        foo: str
        bar: str

    class GetManyModel(BaseModel, Generic[T]):
        res: list[T]

    class GetManyModel2(GetManyModel[T], Generic[T]):
        foo: str
        bar: str

    class GetManyModel3(BaseModel, Generic[T]):
        res: dict[str, T]

    class GetManyModel4(BaseModel, Generic[T]):
        res: dict[str, list[T]]

    class PutModel(BaseModel, Generic[T]):
        data: T

    class PutModel2(PutModel[T], Generic[T]):
        foo: str
        bar: str

    class PutManyModel(BaseModel, Generic[T]):
        data: list[T]

    class PutManyModel2(PutManyModel[T], Generic[T]):
        foo: str
        bar: str

    api_models: list[Any] = [
        GetModel,
        GetModel2,
        GetManyModel,
        GetManyModel2,
        GetManyModel3,
        GetManyModel4,
        PutModel,
        PutModel2,
        PutManyModel,
        PutManyModel2,
    ]

    assert len(data_models) == INNER_DATA_MODEL_COUNT + OUTER_DATA_MODEL_COUNT

    def bench():
        concrete_api_models = []
        adapters = []
        for outer_api_model in api_models:
            for data_model in data_models:
                concrete_api_model = outer_api_model[
                    data_model
                ]  # Would be used eg as request or response body in FastAPI
                concrete_api_models.append(concrete_api_model)

                # Emulate FastAPI creating its TypeAdapters
                adapt = TypeAdapter(Annotated[concrete_api_model, FieldInfo(description='foo')])
                adapters.append(adapt)
                adapt = TypeAdapter(Annotated[concrete_api_model, FieldInfo(description='bar')])
                adapters.append(adapt)

        assert len(concrete_api_models) == len(data_models) * len(api_models)
        assert len(adapters) == len(concrete_api_models) * 2

    benchmark(bench)


if __name__ == '__main__':
    # run with `pdm run tests/benchmarks/test_fastapi_startup.py`
    import cProfile
    import sys
    import time

    INNER_DATA_MODEL_COUNT = 50
    OUTER_DATA_MODEL_COUNT = 50
    print(f'Python version: {sys.version}')
    if sys.argv[-1] == 'cProfile':
        cProfile.run(
            'test_fastapi_startup_perf(lambda f: f())',
            sort='tottime',
            filename=Path(__file__).name.strip('.py') + '.cprof',
        )
    else:
        start = time.perf_counter()
        test_fastapi_startup_perf(lambda f: f())
        end = time.perf_counter()
        print(f'Time taken: {end - start:.2f}s')
